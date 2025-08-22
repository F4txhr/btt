#include <jni.h>
#include "audio_engine.h"
#include "dsp_processor.h"
#include "equalizer.h"
#include "visualizer.h"
#include <android/log.h>
#include <memory>

#define LOG_TAG "AudioPlayerJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Global instances
static std::unique_ptr<AudioEngine> g_audioEngine;
static std::unique_ptr<DSPProcessor> g_dspProcessor;
static std::unique_ptr<Equalizer> g_equalizer;
static std::unique_ptr<Visualizer> g_visualizer;

extern "C" {

JNIEXPORT jboolean JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_initAudioEngine(JNIEnv *env, jobject thiz) {
    try {
        g_audioEngine = std::make_unique<AudioEngine>();
        g_dspProcessor = std::make_unique<DSPProcessor>();
        g_equalizer = std::make_unique<Equalizer>();
        g_visualizer = std::make_unique<Visualizer>();
        
        LOGI("Audio engine initialized successfully");
        return JNI_TRUE;
    } catch (const std::exception& e) {
        LOGE("Failed to initialize audio engine: %s", e.what());
        return JNI_FALSE;
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_destroyAudioEngine(JNIEnv *env, jobject thiz) {
    g_audioEngine.reset();
    g_dspProcessor.reset();
    g_equalizer.reset();
    g_visualizer.reset();
    LOGI("Audio engine destroyed");
}

JNIEXPORT jboolean JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_startAudioEngine(JNIEnv *env, jobject thiz) {
    if (!g_audioEngine) {
        LOGE("Audio engine not initialized");
        return JNI_FALSE;
    }
    return g_audioEngine->start() ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_stopAudioEngine(JNIEnv *env, jobject thiz) {
    if (g_audioEngine) {
        g_audioEngine->stop();
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_pauseAudioEngine(JNIEnv *env, jobject thiz) {
    if (g_audioEngine) {
        g_audioEngine->pause();
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_resumeAudioEngine(JNIEnv *env, jobject thiz) {
    if (g_audioEngine) {
        g_audioEngine->resume();
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setVolume(JNIEnv *env, jobject thiz, jfloat volume) {
    if (g_audioEngine) {
        g_audioEngine->setVolume(volume);
    }
}

JNIEXPORT jfloat JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getVolume(JNIEnv *env, jobject thiz) {
    if (g_audioEngine) {
        return g_audioEngine->getVolume();
    }
    return 1.0f;
}

JNIEXPORT jboolean JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_isHighResSupported(JNIEnv *env, jobject thiz) {
    if (g_audioEngine) {
        return g_audioEngine->isHighResSupported() ? JNI_TRUE : JNI_FALSE;
    }
    return JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_enableHighRes(JNIEnv *env, jobject thiz, jboolean enable) {
    if (g_audioEngine) {
        g_audioEngine->enableHighRes(enable);
    }
}

// Equalizer functions
JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setGraphicEQBand(JNIEnv *env, jobject thiz, jint band, jfloat gain) {
    if (g_equalizer) {
        g_equalizer->setGraphicEQBand(band, gain);
    }
}

JNIEXPORT jfloat JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getGraphicEQBand(JNIEnv *env, jobject thiz, jint band) {
    if (g_equalizer) {
        return g_equalizer->getGraphicEQBand(band);
    }
    return 0.0f;
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_resetGraphicEQ(JNIEnv *env, jobject thiz) {
    if (g_equalizer) {
        g_equalizer->resetGraphicEQ();
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setEqualizerEnabled(JNIEnv *env, jobject thiz, jboolean enabled) {
    if (g_equalizer) {
        g_equalizer->setEnabled(enabled);
    }
}

// DSP functions
JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setPreamp(JNIEnv *env, jobject thiz, jfloat gain) {
    if (g_dspProcessor) {
        g_dspProcessor->setPreamp(gain);
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setLimiterThreshold(JNIEnv *env, jobject thiz, jfloat threshold) {
    if (g_dspProcessor) {
        g_dspProcessor->setLimiterThreshold(threshold);
    }
}

JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setLimiterRatio(JNIEnv *env, jobject thiz, jfloat ratio) {
    if (g_dspProcessor) {
        g_dspProcessor->setLimiterRatio(ratio);
    }
}

// Visualizer functions
JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_setVisualizerEnabled(JNIEnv *env, jobject thiz, jboolean enabled) {
    if (g_visualizer) {
        g_visualizer->setEnabled(enabled);
    }
}

JNIEXPORT jfloatArray JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getSpectrum(JNIEnv *env, jobject thiz) {
    if (!g_visualizer) {
        return nullptr;
    }
    
    const auto& spectrum = g_visualizer->getSpectrum();
    jfloatArray result = env->NewFloatArray(spectrum.size());
    env->SetFloatArrayRegion(result, 0, spectrum.size(), spectrum.data());
    return result;
}

JNIEXPORT jfloatArray JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getWaveform(JNIEnv *env, jobject thiz) {
    if (!g_visualizer) {
        return nullptr;
    }
    
    const auto& waveform = g_visualizer->getWaveform();
    jfloatArray result = env->NewFloatArray(waveform.size());
    env->SetFloatArrayRegion(result, 0, waveform.size(), waveform.data());
    return result;
}

JNIEXPORT jfloat JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getLeftPeak(JNIEnv *env, jobject thiz) {
    if (g_visualizer) {
        return g_visualizer->getLeftPeak();
    }
    return 0.0f;
}

JNIEXPORT jfloat JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getRightPeak(JNIEnv *env, jobject thiz) {
    if (g_visualizer) {
        return g_visualizer->getRightPeak();
    }
    return 0.0f;
}

JNIEXPORT jfloat JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_getRMS(JNIEnv *env, jobject thiz) {
    if (g_visualizer) {
        return g_visualizer->getRMS();
    }
    return 0.0f;
}

// Audio processing function (called from audio callback)
JNIEXPORT void JNICALL
Java_com_audioplayerpro_audio_core_AudioPlayerNative_processAudio(JNIEnv *env, jobject thiz, jfloatArray input, jfloatArray output, jint numFrames, jint numChannels) {
    if (!g_dspProcessor || !g_equalizer || !g_visualizer) {
        return;
    }
    
    jfloat* inputPtr = env->GetFloatArrayElements(input, nullptr);
    jfloat* outputPtr = env->GetFloatArrayElements(output, nullptr);
    
    // Process audio through DSP chain
    g_dspProcessor->processAudio(inputPtr, outputPtr, numFrames, numChannels);
    g_equalizer->processAudio(outputPtr, outputPtr, numFrames, numChannels);
    g_visualizer->processAudio(outputPtr, numFrames, numChannels);
    
    env->ReleaseFloatArrayElements(input, inputPtr, JNI_ABORT);
    env->ReleaseFloatArrayElements(output, outputPtr, 0);
}

} // extern "C"