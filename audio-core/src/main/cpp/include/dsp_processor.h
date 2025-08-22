#ifndef DSP_PROCESSOR_H
#define DSP_PROCESSOR_H

#include <vector>
#include <memory>

// DSP Filter types
enum class FilterType {
    LOW_PASS,
    HIGH_PASS,
    BAND_PASS,
    LOW_SHELF,
    HIGH_SHELF,
    PEAKING
};

// DSP Effect types
enum class EffectType {
    REVERB,
    DELAY,
    CHORUS,
    STEREO_WIDENER,
    LIMITER,
    COMPRESSOR
};

struct FilterParams {
    FilterType type;
    float frequency;
    float q;
    float gain;
};

struct EffectParams {
    EffectType type;
    float mix;
    float param1;
    float param2;
    float param3;
};

class DSPProcessor {
public:
    DSPProcessor();
    ~DSPProcessor();

    // Main processing function
    void processAudio(float* input, float* output, int numFrames, int numChannels);

    // Filter management
    void addFilter(const FilterParams& params);
    void removeFilter(int index);
    void updateFilter(int index, const FilterParams& params);
    void clearFilters();

    // Effect management
    void addEffect(const EffectParams& params);
    void removeEffect(int index);
    void updateEffect(int index, const EffectParams& params);
    void clearEffects();

    // Preamp and limiter
    void setPreamp(float gain);
    void setLimiterThreshold(float threshold);
    void setLimiterRatio(float ratio);

    // Sample rate
    void setSampleRate(int sampleRate);

private:
    std::vector<FilterParams> filters_;
    std::vector<EffectParams> effects_;
    
    float preampGain_;
    float limiterThreshold_;
    float limiterRatio_;
    int sampleRate_;
    
    // Processing buffers
    std::vector<float> tempBuffer_;
    
    // Apply filters
    void applyFilters(float* buffer, int numFrames, int numChannels);
    
    // Apply effects
    void applyEffects(float* buffer, int numFrames, int numChannels);
    
    // Apply preamp and limiter
    void applyPreampAndLimiter(float* buffer, int numFrames, int numChannels);
};

#endif // DSP_PROCESSOR_H