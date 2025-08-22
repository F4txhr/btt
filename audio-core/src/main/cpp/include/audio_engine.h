#ifndef AUDIO_ENGINE_H
#define AUDIO_ENGINE_H

#include <oboe/Oboe.h>
#include <memory>
#include <vector>
#include <mutex>

class AudioEngine : public oboe::AudioStreamDataCallback {
public:
    AudioEngine();
    ~AudioEngine();

    // Audio stream callback
    oboe::DataCallbackResult onAudioReady(oboe::AudioStream *audioStream, void *audioData, int32_t numFrames) override;

    // Engine control
    bool start();
    void stop();
    void pause();
    void resume();

    // Audio format settings
    void setSampleRate(int32_t sampleRate);
    void setChannelCount(int32_t channelCount);
    void setAudioFormat(oboe::AudioFormat format);

    // High-resolution audio support
    bool isHighResSupported();
    void enableHighRes(bool enable);

    // Volume control
    void setVolume(float volume);
    float getVolume() const;

    // Audio data input
    void setAudioData(const std::vector<float>& data);
    void clearAudioData();

private:
    std::unique_ptr<oboe::AudioStream> audioStream_;
    std::vector<float> audioBuffer_;
    std::mutex bufferMutex_;
    
    int32_t sampleRate_;
    int32_t channelCount_;
    oboe::AudioFormat audioFormat_;
    float volume_;
    bool isPlaying_;
    bool highResEnabled_;
    
    // High-resolution audio settings
    static constexpr int32_t HIGH_RES_SAMPLE_RATE = 192000;
    static constexpr int32_t HIGH_RES_BIT_DEPTH = 32;
};

#endif // AUDIO_ENGINE_H