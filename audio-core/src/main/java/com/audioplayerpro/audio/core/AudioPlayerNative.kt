package com.audioplayerpro.audio.core

class AudioPlayerNative {
    companion object {
        init {
            System.loadLibrary("audioplayer-core")
        }
    }

    // Audio Engine functions
    external fun initAudioEngine(): Boolean
    external fun destroyAudioEngine()
    external fun startAudioEngine(): Boolean
    external fun stopAudioEngine()
    external fun pauseAudioEngine()
    external fun resumeAudioEngine()
    
    // Volume control
    external fun setVolume(volume: Float)
    external fun getVolume(): Float
    
    // High-resolution audio
    external fun isHighResSupported(): Boolean
    external fun enableHighRes(enable: Boolean)
    
    // Equalizer functions
    external fun setGraphicEQBand(band: Int, gain: Float)
    external fun getGraphicEQBand(band: Int): Float
    external fun resetGraphicEQ()
    external fun setEqualizerEnabled(enabled: Boolean)
    
    // DSP functions
    external fun setPreamp(gain: Float)
    external fun setLimiterThreshold(threshold: Float)
    external fun setLimiterRatio(ratio: Float)
    
    // Visualizer functions
    external fun setVisualizerEnabled(enabled: Boolean)
    external fun getSpectrum(): FloatArray?
    external fun getWaveform(): FloatArray?
    external fun getLeftPeak(): Float
    external fun getRightPeak(): Float
    external fun getRMS(): Float
    
    // Audio processing
    external fun processAudio(input: FloatArray, output: FloatArray, numFrames: Int, numChannels: Int)
}