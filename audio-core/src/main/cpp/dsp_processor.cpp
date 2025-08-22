#include "dsp_processor.h"
#include <algorithm>
#include <cmath>

DSPProcessor::DSPProcessor()
    : preampGain_(1.0f)
    , limiterThreshold_(0.95f)
    , limiterRatio_(10.0f)
    , sampleRate_(48000) {
}

DSPProcessor::~DSPProcessor() {
}

void DSPProcessor::processAudio(float* input, float* output, int numFrames, int numChannels) {
    if (tempBuffer_.size() < numFrames * numChannels) {
        tempBuffer_.resize(numFrames * numChannels);
    }

    // Copy input to temp buffer
    std::copy(input, input + numFrames * numChannels, tempBuffer_.data());

    // Apply filters
    applyFilters(tempBuffer_.data(), numFrames, numChannels);

    // Apply effects
    applyEffects(tempBuffer_.data(), numFrames, numChannels);

    // Apply preamp and limiter
    applyPreampAndLimiter(tempBuffer_.data(), numFrames, numChannels);

    // Copy to output
    std::copy(tempBuffer_.data(), tempBuffer_.data() + numFrames * numChannels, output);
}

void DSPProcessor::addFilter(const FilterParams& params) {
    filters_.push_back(params);
}

void DSPProcessor::removeFilter(int index) {
    if (index >= 0 && index < static_cast<int>(filters_.size())) {
        filters_.erase(filters_.begin() + index);
    }
}

void DSPProcessor::updateFilter(int index, const FilterParams& params) {
    if (index >= 0 && index < static_cast<int>(filters_.size())) {
        filters_[index] = params;
    }
}

void DSPProcessor::clearFilters() {
    filters_.clear();
}

void DSPProcessor::addEffect(const EffectParams& params) {
    effects_.push_back(params);
}

void DSPProcessor::removeEffect(int index) {
    if (index >= 0 && index < static_cast<int>(effects_.size())) {
        effects_.erase(effects_.begin() + index);
    }
}

void DSPProcessor::updateEffect(int index, const EffectParams& params) {
    if (index >= 0 && index < static_cast<int>(effects_.size())) {
        effects_[index] = params;
    }
}

void DSPProcessor::clearEffects() {
    effects_.clear();
}

void DSPProcessor::setPreamp(float gain) {
    preampGain_ = gain;
}

void DSPProcessor::setLimiterThreshold(float threshold) {
    limiterThreshold_ = threshold;
}

void DSPProcessor::setLimiterRatio(float ratio) {
    limiterRatio_ = ratio;
}

void DSPProcessor::setSampleRate(int sampleRate) {
    sampleRate_ = sampleRate;
}

void DSPProcessor::applyFilters(float* buffer, int numFrames, int numChannels) {
    for (const auto& filter : filters_) {
        // Simple IIR filter implementation
        float w0 = 2.0f * M_PI * filter.frequency / sampleRate_;
        float alpha = std::sin(w0) / (2.0f * filter.q);
        
        float b0, b1, b2, a0, a1, a2;
        
        switch (filter.type) {
            case FilterType::LOW_PASS: {
                float cosw0 = std::cos(w0);
                b0 = (1.0f - cosw0) / 2.0f;
                b1 = 1.0f - cosw0;
                b2 = (1.0f - cosw0) / 2.0f;
                a0 = 1.0f + alpha;
                a1 = -2.0f * cosw0;
                a2 = 1.0f - alpha;
                break;
            }
            case FilterType::HIGH_PASS: {
                float cosw0 = std::cos(w0);
                b0 = (1.0f + cosw0) / 2.0f;
                b1 = -(1.0f + cosw0);
                b2 = (1.0f + cosw0) / 2.0f;
                a0 = 1.0f + alpha;
                a1 = -2.0f * cosw0;
                a2 = 1.0f - alpha;
                break;
            }
            case FilterType::LOW_SHELF: {
                float A = std::pow(10.0f, filter.gain / 40.0f);
                float cosw0 = std::cos(w0);
                float sinw0 = std::sin(w0);
                float S = 1.0f;
                float alpha = sinw0 / 2.0f * std::sqrt((A + 1.0f / A) * (1.0f / S - 1.0f) + 2.0f);
                
                b0 = A * ((A + 1.0f) - (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha);
                b1 = 2.0f * A * ((A - 1.0f) - (A + 1.0f) * cosw0);
                b2 = A * ((A + 1.0f) - (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha);
                a0 = (A + 1.0f) + (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha;
                a1 = -2.0f * ((A - 1.0f) + (A + 1.0f) * cosw0);
                a2 = (A + 1.0f) + (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha;
                break;
            }
            case FilterType::HIGH_SHELF: {
                float A = std::pow(10.0f, filter.gain / 40.0f);
                float cosw0 = std::cos(w0);
                float sinw0 = std::sin(w0);
                float S = 1.0f;
                float alpha = sinw0 / 2.0f * std::sqrt((A + 1.0f / A) * (1.0f / S - 1.0f) + 2.0f);
                
                b0 = A * ((A + 1.0f) + (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha);
                b1 = -2.0f * A * ((A - 1.0f) + (A + 1.0f) * cosw0);
                b2 = A * ((A + 1.0f) + (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha);
                a0 = (A + 1.0f) - (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha;
                a1 = 2.0f * ((A - 1.0f) - (A + 1.0f) * cosw0);
                a2 = (A + 1.0f) - (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha;
                break;
            }
            case FilterType::PEAKING: {
                float A = std::pow(10.0f, filter.gain / 40.0f);
                float cosw0 = std::cos(w0);
                float sinw0 = std::sin(w0);
                float alpha = sinw0 / (2.0f * filter.q);
                
                b0 = 1.0f + alpha * A;
                b1 = -2.0f * cosw0;
                b2 = 1.0f - alpha * A;
                a0 = 1.0f + alpha / A;
                a1 = -2.0f * cosw0;
                a2 = 1.0f - alpha / A;
                break;
            }
            default:
                continue;
        }
        
        // Normalize coefficients
        b0 /= a0;
        b1 /= a0;
        b2 /= a0;
        a1 /= a0;
        a2 /= a0;
        
        // Apply filter (simple IIR implementation)
        static std::vector<float> x1(2, 0.0f), x2(2, 0.0f);
        static std::vector<float> y1(2, 0.0f), y2(2, 0.0f);
        
        for (int frame = 0; frame < numFrames; ++frame) {
            for (int ch = 0; ch < numChannels; ++ch) {
                int idx = frame * numChannels + ch;
                float x0 = buffer[idx];
                
                float y0 = b0 * x0 + b1 * x1[ch] + b2 * x2[ch] - a1 * y1[ch] - a2 * y2[ch];
                
                x2[ch] = x1[ch];
                x1[ch] = x0;
                y2[ch] = y1[ch];
                y1[ch] = y0;
                
                buffer[idx] = y0;
            }
        }
    }
}

void DSPProcessor::applyEffects(float* buffer, int numFrames, int numChannels) {
    for (const auto& effect : effects_) {
        switch (effect.type) {
            case EffectType::REVERB: {
                // Simple reverb implementation
                static std::vector<float> delayBuffer(44100, 0.0f); // 1 second delay
                static int delayIndex = 0;
                
                for (int i = 0; i < numFrames * numChannels; ++i) {
                    float delayed = delayBuffer[delayIndex];
                    delayBuffer[delayIndex] = buffer[i];
                    buffer[i] = buffer[i] * (1.0f - effect.mix) + delayed * effect.mix * 0.5f;
                    delayIndex = (delayIndex + 1) % delayBuffer.size();
                }
                break;
            }
            case EffectType::DELAY: {
                // Simple delay implementation
                int delaySamples = static_cast<int>(effect.param1 * sampleRate_);
                static std::vector<float> delayBuffer(44100, 0.0f);
                static int delayIndex = 0;
                
                for (int i = 0; i < numFrames * numChannels; ++i) {
                    float delayed = delayBuffer[(delayIndex - delaySamples + delayBuffer.size()) % delayBuffer.size()];
                    delayBuffer[delayIndex] = buffer[i];
                    buffer[i] = buffer[i] + delayed * effect.mix;
                    delayIndex = (delayIndex + 1) % delayBuffer.size();
                }
                break;
            }
            case EffectType::STEREO_WIDENER: {
                // Stereo widener
                if (numChannels == 2) {
                    for (int frame = 0; frame < numFrames; ++frame) {
                        float left = buffer[frame * 2];
                        float right = buffer[frame * 2 + 1];
                        
                        float mid = (left + right) * 0.5f;
                        float side = (left - right) * 0.5f;
                        
                        side *= effect.param1; // Width parameter
                        
                        buffer[frame * 2] = mid + side;
                        buffer[frame * 2 + 1] = mid - side;
                    }
                }
                break;
            }
            case EffectType::LIMITER: {
                // Simple limiter
                for (int i = 0; i < numFrames * numChannels; ++i) {
                    float absVal = std::abs(buffer[i]);
                    if (absVal > limiterThreshold_) {
                        float gain = limiterThreshold_ / absVal;
                        buffer[i] *= gain;
                    }
                }
                break;
            }
            default:
                break;
        }
    }
}

void DSPProcessor::applyPreampAndLimiter(float* buffer, int numFrames, int numChannels) {
    for (int i = 0; i < numFrames * numChannels; ++i) {
        // Apply preamp
        buffer[i] *= preampGain_;
        
        // Apply limiter
        float absVal = std::abs(buffer[i]);
        if (absVal > limiterThreshold_) {
            float gain = limiterThreshold_ + (absVal - limiterThreshold_) / limiterRatio_;
            gain = gain / absVal;
            buffer[i] *= gain;
        }
    }
}