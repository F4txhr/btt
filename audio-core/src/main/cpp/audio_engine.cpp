#include "audio_engine.h"
#include <android/log.h>
#include <algorithm>

#define LOG_TAG "AudioEngine"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

AudioEngine::AudioEngine()
    : sampleRate_(48000)
    , channelCount_(2)
    , audioFormat_(oboe::AudioFormat::Float)
    , volume_(1.0f)
    , isPlaying_(false)
    , highResEnabled_(false) {
    
    LOGI("AudioEngine created");
}

AudioEngine::~AudioEngine() {
    stop();
    LOGI("AudioEngine destroyed");
}

oboe::DataCallbackResult AudioEngine::onAudioReady(oboe::AudioStream *audioStream, void *audioData, int32_t numFrames) {
    if (!isPlaying_ || audioBuffer_.empty()) {
        // Fill with silence
        std::fill_n(static_cast<float*>(audioData), numFrames * channelCount_, 0.0f);
        return oboe::DataCallbackResult::Continue;
    }

    std::lock_guard<std::mutex> lock(bufferMutex_);
    
    float* output = static_cast<float*>(audioData);
    int32_t framesToCopy = std::min(numFrames, static_cast<int32_t>(audioBuffer_.size() / channelCount_));
    
    // Copy audio data with volume control
    for (int32_t i = 0; i < framesToCopy * channelCount_; ++i) {
        output[i] = audioBuffer_[i] * volume_;
    }
    
    // Fill remaining frames with silence
    for (int32_t i = framesToCopy * channelCount_; i < numFrames * channelCount_; ++i) {
        output[i] = 0.0f;
    }
    
    return oboe::DataCallbackResult::Continue;
}

bool AudioEngine::start() {
    if (isPlaying_) {
        return true;
    }

    oboe::AudioStreamBuilder builder;
    builder.setCallback(this)
           .setDirection(oboe::Direction::Output)
           .setChannelCount(channelCount_)
           .setFormat(audioFormat_)
           .setSampleRate(sampleRate_)
           .setPerformanceMode(oboe::PerformanceMode::LowLatency)
           .setSharingMode(oboe::SharingMode::Exclusive);

    if (highResEnabled_) {
        builder.setSampleRate(HIGH_RES_SAMPLE_RATE);
        builder.setFormat(oboe::AudioFormat::Float);
    }

    oboe::Result result = builder.openStream(audioStream_);
    if (result != oboe::Result::OK) {
        LOGE("Failed to open audio stream: %s", oboe::convertToText(result));
        return false;
    }

    result = audioStream_->requestStart();
    if (result != oboe::Result::OK) {
        LOGE("Failed to start audio stream: %s", oboe::convertToText(result));
        return false;
    }

    isPlaying_ = true;
    LOGI("Audio engine started");
    return true;
}

void AudioEngine::stop() {
    if (!isPlaying_) {
        return;
    }

    if (audioStream_) {
        audioStream_->requestStop();
        audioStream_->close();
        audioStream_.reset();
    }

    isPlaying_ = false;
    LOGI("Audio engine stopped");
}

void AudioEngine::pause() {
    if (audioStream_ && isPlaying_) {
        audioStream_->requestPause();
        isPlaying_ = false;
        LOGI("Audio engine paused");
    }
}

void AudioEngine::resume() {
    if (audioStream_ && !isPlaying_) {
        audioStream_->requestStart();
        isPlaying_ = true;
        LOGI("Audio engine resumed");
    }
}

void AudioEngine::setSampleRate(int32_t sampleRate) {
    sampleRate_ = sampleRate;
    if (audioStream_) {
        audioStream_->setSampleRate(sampleRate);
    }
}

void AudioEngine::setChannelCount(int32_t channelCount) {
    channelCount_ = channelCount;
}

void AudioEngine::setAudioFormat(oboe::AudioFormat format) {
    audioFormat_ = format;
}

bool AudioEngine::isHighResSupported() {
    // Check if device supports high-resolution audio
    oboe::AudioStreamBuilder builder;
    builder.setDirection(oboe::Direction::Output)
           .setChannelCount(2)
           .setFormat(oboe::AudioFormat::Float)
           .setSampleRate(HIGH_RES_SAMPLE_RATE);

    std::unique_ptr<oboe::AudioStream> testStream;
    oboe::Result result = builder.openStream(testStream);
    
    if (result == oboe::Result::OK) {
        testStream->close();
        return true;
    }
    
    return false;
}

void AudioEngine::enableHighRes(bool enable) {
    highResEnabled_ = enable;
    if (enable) {
        sampleRate_ = HIGH_RES_SAMPLE_RATE;
        audioFormat_ = oboe::AudioFormat::Float;
    } else {
        sampleRate_ = 48000;
        audioFormat_ = oboe::AudioFormat::Float;
    }
}

void AudioEngine::setVolume(float volume) {
    volume_ = std::clamp(volume, 0.0f, 1.0f);
}

float AudioEngine::getVolume() const {
    return volume_;
}

void AudioEngine::setAudioData(const std::vector<float>& data) {
    std::lock_guard<std::mutex> lock(bufferMutex_);
    audioBuffer_ = data;
}

void AudioEngine::clearAudioData() {
    std::lock_guard<std::mutex> lock(bufferMutex_);
    audioBuffer_.clear();
}