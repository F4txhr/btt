#include "equalizer.h"
#include <algorithm>
#include <cmath>

Equalizer::Equalizer()
    : sampleRate_(48000)
    , enabled_(false) {
    
    // Initialize graphic EQ gains to 0 dB
    graphicEQGains_.fill(0.0f);
    
    // Initialize filter coefficients
    updateGraphicEQCoeffs();
}

Equalizer::~Equalizer() {
}

void Equalizer::setGraphicEQBand(int band, float gain) {
    if (band >= 0 && band < 10) {
        graphicEQGains_[band] = std::clamp(gain, -12.0f, 12.0f);
        updateGraphicEQCoeffs();
    }
}

float Equalizer::getGraphicEQBand(int band) const {
    if (band >= 0 && band < 10) {
        return graphicEQGains_[band];
    }
    return 0.0f;
}

void Equalizer::setGraphicEQBands(const std::array<float, 10>& gains) {
    graphicEQGains_ = gains;
    for (auto& gain : graphicEQGains_) {
        gain = std::clamp(gain, -12.0f, 12.0f);
    }
    updateGraphicEQCoeffs();
}

std::array<float, 10> Equalizer::getGraphicEQBands() const {
    return graphicEQGains_;
}

void Equalizer::resetGraphicEQ() {
    graphicEQGains_.fill(0.0f);
    updateGraphicEQCoeffs();
}

void Equalizer::addParametricBand(const ParametricBand& band) {
    parametricBands_.push_back(band);
    updateParametricEQCoeffs();
}

void Equalizer::removeParametricBand(int index) {
    if (index >= 0 && index < static_cast<int>(parametricBands_.size())) {
        parametricBands_.erase(parametricBands_.begin() + index);
        updateParametricEQCoeffs();
    }
}

void Equalizer::updateParametricBand(int index, const ParametricBand& band) {
    if (index >= 0 && index < static_cast<int>(parametricBands_.size())) {
        parametricBands_[index] = band;
        updateParametricEQCoeffs();
    }
}

void Equalizer::clearParametricBands() {
    parametricBands_.clear();
}

void Equalizer::processAudio(float* input, float* output, int numFrames, int numChannels) {
    if (!enabled_) {
        // Just copy input to output
        std::copy(input, input + numFrames * numChannels, output);
        return;
    }

    // Copy input to output buffer
    std::copy(input, input + numFrames * numChannels, output);

    // Apply graphic EQ
    applyGraphicEQ(output, numFrames, numChannels);

    // Apply parametric EQ
    applyParametricEQ(output, numFrames, numChannels);
}

void Equalizer::setSampleRate(int sampleRate) {
    sampleRate_ = sampleRate;
    updateGraphicEQCoeffs();
    updateParametricEQCoeffs();
}

void Equalizer::setEnabled(bool enabled) {
    enabled_ = enabled;
}

bool Equalizer::isEnabled() const {
    return enabled_;
}

void Equalizer::loadPreset(const std::string& name) {
    // TODO: Implement preset loading from storage
    // For now, just reset to flat response
    resetGraphicEQ();
    clearParametricBands();
}

void Equalizer::savePreset(const std::string& name) {
    // TODO: Implement preset saving to storage
}

std::vector<std::string> Equalizer::getPresetNames() const {
    // TODO: Implement preset names retrieval
    return {"Flat", "Bass Boost", "Treble Boost", "Vocal Boost"};
}

void Equalizer::updateGraphicEQCoeffs() {
    for (int i = 0; i < 10; ++i) {
        float frequency = GRAPHIC_EQ_FREQUENCIES[i];
        float gain = graphicEQGains_[i];
        
        if (std::abs(gain) < 0.1f) {
            // Flat response
            graphicEQCoeffs_[i] = {1.0f, 0.0f, 0.0f, 0.0f, 0.0f};
        } else {
            // Design filter based on frequency and gain
            if (frequency < 1000.0f) {
                // Low frequency - use low shelf
                graphicEQCoeffs_[i] = designLowShelf(frequency, gain, 1.0f);
            } else {
                // High frequency - use high shelf
                graphicEQCoeffs_[i] = designHighShelf(frequency, gain, 1.0f);
            }
        }
    }
}

void Equalizer::updateParametricEQCoeffs() {
    // Parametric EQ coefficients are calculated on-the-fly
    // since they can be dynamically changed
}

void Equalizer::applyGraphicEQ(float* buffer, int numFrames, int numChannels) {
    for (int band = 0; band < 10; ++band) {
        const auto& coeffs = graphicEQCoeffs_[band];
        
        // Skip if flat response
        if (std::abs(coeffs.b0 - 1.0f) < 0.001f && std::abs(coeffs.b1) < 0.001f && 
            std::abs(coeffs.b2) < 0.001f && std::abs(coeffs.a1) < 0.001f && std::abs(coeffs.a2) < 0.001f) {
            continue;
        }
        
        // Apply IIR filter
        static std::vector<float> x1(2, 0.0f), x2(2, 0.0f);
        static std::vector<float> y1(2, 0.0f), y2(2, 0.0f);
        
        for (int frame = 0; frame < numFrames; ++frame) {
            for (int ch = 0; ch < numChannels; ++ch) {
                int idx = frame * numChannels + ch;
                float x0 = buffer[idx];
                
                float y0 = coeffs.b0 * x0 + coeffs.b1 * x1[ch] + coeffs.b2 * x2[ch] 
                          - coeffs.a1 * y1[ch] - coeffs.a2 * y2[ch];
                
                x2[ch] = x1[ch];
                x1[ch] = x0;
                y2[ch] = y1[ch];
                y1[ch] = y0;
                
                buffer[idx] = y0;
            }
        }
    }
}

void Equalizer::applyParametricEQ(float* buffer, int numFrames, int numChannels) {
    for (const auto& band : parametricBands_) {
        if (!band.enabled) continue;
        
        // Design filter coefficients for this band
        auto coeffs = designPeaking(band.frequency, band.gain, band.q);
        
        // Apply IIR filter
        static std::vector<float> x1(2, 0.0f), x2(2, 0.0f);
        static std::vector<float> y1(2, 0.0f), y2(2, 0.0f);
        
        for (int frame = 0; frame < numFrames; ++frame) {
            for (int ch = 0; ch < numChannels; ++ch) {
                int idx = frame * numChannels + ch;
                float x0 = buffer[idx];
                
                float y0 = coeffs.b0 * x0 + coeffs.b1 * x1[ch] + coeffs.b2 * x2[ch] 
                          - coeffs.a1 * y1[ch] - coeffs.a2 * y2[ch];
                
                x2[ch] = x1[ch];
                x1[ch] = x0;
                y2[ch] = y1[ch];
                y1[ch] = y0;
                
                buffer[idx] = y0;
            }
        }
    }
}

Equalizer::FilterCoeffs Equalizer::designLowShelf(float frequency, float gain, float q) {
    float w0 = 2.0f * M_PI * frequency / sampleRate_;
    float A = std::pow(10.0f, gain / 40.0f);
    float cosw0 = std::cos(w0);
    float sinw0 = std::sin(w0);
    float S = 1.0f;
    float alpha = sinw0 / 2.0f * std::sqrt((A + 1.0f / A) * (1.0f / S - 1.0f) + 2.0f);
    
    FilterCoeffs coeffs;
    coeffs.b0 = A * ((A + 1.0f) - (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha);
    coeffs.b1 = 2.0f * A * ((A - 1.0f) - (A + 1.0f) * cosw0);
    coeffs.b2 = A * ((A + 1.0f) - (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha);
    float a0 = (A + 1.0f) + (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha;
    coeffs.a1 = -2.0f * ((A - 1.0f) + (A + 1.0f) * cosw0);
    coeffs.a2 = (A + 1.0f) + (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha;
    
    // Normalize
    coeffs.b0 /= a0;
    coeffs.b1 /= a0;
    coeffs.b2 /= a0;
    coeffs.a1 /= a0;
    coeffs.a2 /= a0;
    
    return coeffs;
}

Equalizer::FilterCoeffs Equalizer::designHighShelf(float frequency, float gain, float q) {
    float w0 = 2.0f * M_PI * frequency / sampleRate_;
    float A = std::pow(10.0f, gain / 40.0f);
    float cosw0 = std::cos(w0);
    float sinw0 = std::sin(w0);
    float S = 1.0f;
    float alpha = sinw0 / 2.0f * std::sqrt((A + 1.0f / A) * (1.0f / S - 1.0f) + 2.0f);
    
    FilterCoeffs coeffs;
    coeffs.b0 = A * ((A + 1.0f) + (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha);
    coeffs.b1 = -2.0f * A * ((A - 1.0f) + (A + 1.0f) * cosw0);
    coeffs.b2 = A * ((A + 1.0f) + (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha);
    float a0 = (A + 1.0f) - (A - 1.0f) * cosw0 + 2.0f * std::sqrt(A) * alpha;
    coeffs.a1 = 2.0f * ((A - 1.0f) - (A + 1.0f) * cosw0);
    coeffs.a2 = (A + 1.0f) - (A - 1.0f) * cosw0 - 2.0f * std::sqrt(A) * alpha;
    
    // Normalize
    coeffs.b0 /= a0;
    coeffs.b1 /= a0;
    coeffs.b2 /= a0;
    coeffs.a1 /= a0;
    coeffs.a2 /= a0;
    
    return coeffs;
}

Equalizer::FilterCoeffs Equalizer::designPeaking(float frequency, float gain, float q) {
    float w0 = 2.0f * M_PI * frequency / sampleRate_;
    float A = std::pow(10.0f, gain / 40.0f);
    float cosw0 = std::cos(w0);
    float sinw0 = std::sin(w0);
    float alpha = sinw0 / (2.0f * q);
    
    FilterCoeffs coeffs;
    coeffs.b0 = 1.0f + alpha * A;
    coeffs.b1 = -2.0f * cosw0;
    coeffs.b2 = 1.0f - alpha * A;
    float a0 = 1.0f + alpha / A;
    coeffs.a1 = -2.0f * cosw0;
    coeffs.a2 = 1.0f - alpha / A;
    
    // Normalize
    coeffs.b0 /= a0;
    coeffs.b1 /= a0;
    coeffs.b2 /= a0;
    coeffs.a1 /= a0;
    coeffs.a2 /= a0;
    
    return coeffs;
}