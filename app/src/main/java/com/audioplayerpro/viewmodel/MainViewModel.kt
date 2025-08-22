package com.audioplayerpro.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.audioplayerpro.audio.core.AudioPlayerNative
import com.audioplayerpro.audio.ml.StemSeparationWorker
import com.audioplayerpro.billing.BillingManager
import com.audioplayerpro.data.AudioDatabase
import com.audioplayerpro.data.AudioTrack
import com.audioplayerpro.data.EQPreset
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.io.File

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val audioPlayer = AudioPlayerNative()
    private val billingManager = BillingManager(application)
    private val database = AudioDatabase.getDatabase(application)

    // UI State
    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    private val _currentTrack = MutableStateFlow<AudioTrack?>(null)
    val currentTrack: StateFlow<AudioTrack?> = _currentTrack.asStateFlow()

    private val _volume = MutableStateFlow(1.0f)
    val volume: StateFlow<Float> = _volume.asStateFlow()

    private val _isHighResEnabled = MutableStateFlow(false)
    val isHighResEnabled: StateFlow<Boolean> = _isHighResEnabled.asStateFlow()

    private val _isHighResSupported = MutableStateFlow(false)
    val isHighResSupported: StateFlow<Boolean> = _isHighResSupported.asStateFlow()

    // Equalizer state
    private val _graphicEQGains = MutableStateFlow(List(10) { 0.0f })
    val graphicEQGains: StateFlow<List<Float>> = _graphicEQGains.asStateFlow()

    private val _isEqualizerEnabled = MutableStateFlow(false)
    val isEqualizerEnabled: StateFlow<Boolean> = _isEqualizerEnabled.asStateFlow()

    // Visualizer state
    private val _spectrum = MutableStateFlow(List(64) { 0.0f })
    val spectrum: StateFlow<List<Float>> = _spectrum.asStateFlow()

    private val _waveform = MutableStateFlow(List(2048) { 0.0f })
    val waveform: StateFlow<List<Float>> = _waveform.asStateFlow()

    private val _leftPeak = MutableStateFlow(0.0f)
    val leftPeak: StateFlow<Float> = _leftPeak.asStateFlow()

    private val _rightPeak = MutableStateFlow(0.0f)
    val rightPeak: StateFlow<Float> = _rightPeak.asStateFlow()

    private val _rms = MutableStateFlow(0.0f)
    val rms: StateFlow<Float> = _rms.asStateFlow()

    // Pro features
    val isProUser: StateFlow<Boolean> = billingManager.isProUser

    // Database data
    val allTracks: StateFlow<List<AudioTrack>> = database.audioTrackDao()
        .getAllTracks()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    val freePresets: StateFlow<List<EQPreset>> = database.eqPresetDao()
        .getFreePresets()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    val proPresets: StateFlow<List<EQPreset>> = database.eqPresetDao()
        .getProPresets()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    init {
        // Start visualizer updates
        startVisualizerUpdates()
    }

    fun initializeAudioEngine() {
        viewModelScope.launch {
            val success = audioPlayer.initAudioEngine()
            if (success) {
                _isHighResSupported.value = audioPlayer.isHighResSupported()
                audioPlayer.setVisualizerEnabled(true)
                audioPlayer.setEqualizerEnabled(true)
            }
        }
    }

    fun cleanup() {
        audioPlayer.destroyAudioEngine()
        billingManager.release()
    }

    // Playback controls
    fun play() {
        viewModelScope.launch {
            val success = audioPlayer.startAudioEngine()
            _isPlaying.value = success
        }
    }

    fun pause() {
        audioPlayer.pauseAudioEngine()
        _isPlaying.value = false
    }

    fun stop() {
        audioPlayer.stopAudioEngine()
        _isPlaying.value = false
    }

    fun setVolume(volume: Float) {
        audioPlayer.setVolume(volume)
        _volume.value = volume
    }

    fun enableHighRes(enable: Boolean) {
        audioPlayer.enableHighRes(enable)
        _isHighResEnabled.value = enable
    }

    // Equalizer controls
    fun setGraphicEQBand(band: Int, gain: Float) {
        audioPlayer.setGraphicEQBand(band, gain)
        val newGains = _graphicEQGains.value.toMutableList()
        newGains[band] = gain
        _graphicEQGains.value = newGains
    }

    fun resetGraphicEQ() {
        audioPlayer.resetGraphicEQ()
        _graphicEQGains.value = List(10) { 0.0f }
    }

    fun setEqualizerEnabled(enabled: Boolean) {
        audioPlayer.setEqualizerEnabled(enabled)
        _isEqualizerEnabled.value = enabled
    }

    // DSP controls
    fun setPreamp(gain: Float) {
        audioPlayer.setPreamp(gain)
    }

    fun setLimiterThreshold(threshold: Float) {
        audioPlayer.setLimiterThreshold(threshold)
    }

    fun setLimiterRatio(ratio: Float) {
        audioPlayer.setLimiterRatio(ratio)
    }

    // Visualizer
    private fun startVisualizerUpdates() {
        viewModelScope.launch {
            while (true) {
                kotlinx.coroutines.delay(16) // ~60 FPS
                
                val spectrum = audioPlayer.getSpectrum()
                if (spectrum != null) {
                    _spectrum.value = spectrum.toList()
                }
                
                val waveform = audioPlayer.getWaveform()
                if (waveform != null) {
                    _waveform.value = waveform.toList()
                }
                
                _leftPeak.value = audioPlayer.getLeftPeak()
                _rightPeak.value = audioPlayer.getRightPeak()
                _rms.value = audioPlayer.getRMS()
            }
        }
    }

    // Preset management
    fun savePreset(name: String, isPro: Boolean = false) {
        viewModelScope.launch {
            val preset = EQPreset(
                name = name,
                graphicEQGains = _graphicEQGains.value.joinToString(","),
                parametricBands = "", // TODO: Add parametric bands
                isPro = isPro
            )
            database.eqPresetDao().insertPreset(preset)
        }
    }

    fun loadPreset(preset: EQPreset) {
        viewModelScope.launch {
            val gains = preset.graphicEQGains.split(",").map { it.toFloatOrNull() ?: 0.0f }
            gains.forEachIndexed { index, gain ->
                setGraphicEQBand(index, gain)
            }
        }
    }

    // Stem separation
    fun separateStems(inputFile: File) {
        val outputDir = File(getApplication<Application>().getExternalFilesDir(null), "stems")
        outputDir.mkdirs()
        
        StemSeparationWorker.enqueue(getApplication(), inputFile, outputDir)
    }

    // Billing
    fun launchProPurchase() {
        // This will be handled by the UI
    }

    fun launchProSubscription() {
        // This will be handled by the UI
    }
}