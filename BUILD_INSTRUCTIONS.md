# Audio Player Pro - Build Instructions

## 🚀 Quick Start

### Prerequisites
1. **Android Studio Arctic Fox+** (2023.1.1 or later)
2. **Android SDK** with API level 24+ (Android 7.0)
3. **NDK 25.2.9519653** (for native audio processing)
4. **CMake 3.22.1** (for C++ builds)
5. **Java 17+** (for Kotlin compilation)

### Setup Steps

1. **Clone/Download Project**
   ```bash
   git clone <repository-url>
   cd AudioPlayerPro
   ```

2. **Configure Android SDK**
   - Open Android Studio
   - Go to Settings/Preferences → Appearance & Behavior → System Settings → Android SDK
   - Install Android SDK Platform 24+ (Android 7.0)
   - Install Android SDK Build-Tools
   - Install NDK 25.2.9519653
   - Install CMake 3.22.1

3. **Set Environment Variables**
   ```bash
   export ANDROID_HOME=/path/to/your/android/sdk
   export ANDROID_NDK_HOME=$ANDROID_HOME/ndk/25.2.9519653
   ```

4. **Update local.properties**
   ```properties
   sdk.dir=/path/to/your/android/sdk
   ndk.dir=/path/to/your/android/sdk/ndk/25.2.9519653
   ```

5. **Build Project**
   ```bash
   # Clean and build
   ./gradlew clean build
   
   # Build debug APK
   ./gradlew assembleDebug
   
   # Build release APK
   ./gradlew assembleRelease
   
   # Install on connected device
   ./gradlew installDebug
   ```

## 📱 Project Structure

```
AudioPlayerPro/
├── app/                          # Main application module
│   ├── src/main/
│   │   ├── java/com/audioplayerpro/
│   │   │   ├── ui/              # Jetpack Compose UI
│   │   │   │   ├── components/  # Reusable UI components
│   │   │   │   ├── screens/     # Main app screens
│   │   │   │   └── theme/       # Material 3 theme
│   │   │   ├── viewmodel/       # MVVM ViewModels
│   │   │   ├── data/            # Room database
│   │   │   ├── billing/         # Google Play Billing
│   │   │   └── service/         # Background services
│   │   ├── res/                 # Resources
│   │   └── AndroidManifest.xml  # App manifest
│   └── build.gradle.kts         # App module build config
├── audio-core/                   # Native audio processing
│   ├── src/main/
│   │   ├── cpp/                 # C++ native code
│   │   │   ├── include/         # Header files
│   │   │   ├── audio_engine.cpp # Oboe audio engine
│   │   │   ├── dsp_processor.cpp # DSP processing
│   │   │   ├── equalizer.cpp    # EQ implementation
│   │   │   ├── visualizer.cpp   # FFT visualizer
│   │   │   └── audio_player_jni.cpp # JNI interface
│   │   └── java/                # JNI wrapper
│   └── build.gradle.kts         # Native module config
├── audio-ml/                     # Machine learning module
│   ├── src/main/
│   │   ├── java/                # TensorFlow Lite integration
│   │   └── assets/              # ML models (Spleeter)
│   └── build.gradle.kts         # ML module config
├── gradle/                       # Gradle wrapper
├── build.gradle.kts             # Root build config
├── settings.gradle.kts          # Project settings
├── gradle.properties            # Gradle properties
└── local.properties             # Local SDK paths
```

## 🔧 Build Configuration

### Key Dependencies
- **Kotlin**: 1.9.23
- **Android Gradle Plugin**: 8.5.0
- **Jetpack Compose BOM**: 2024.02.00
- **Media3**: 1.2.1
- **Room**: 2.6.1
- **WorkManager**: 2.9.0
- **Google Play Billing**: 6.1.0
- **TensorFlow Lite**: 2.15.0
- **Oboe**: Included via NDK

### Native Build Settings
- **C++ Standard**: C++17
- **NDK Version**: 25.2.9519653
- **CMake Version**: 3.22.1
- **Target Architectures**: arm64-v8a, armeabi-v7a, x86_64

## 🎵 Features Implemented

### ✅ Core Features
- [x] High-Resolution Audio Playback (192kHz, 32-bit float)
- [x] 10-Band Graphic Equalizer
- [x] Real-Time FFT Visualizer (64 bands)
- [x] Peak Meters (L/R/RMS)
- [x] Background Playback with MediaSession
- [x] Material 3 UI with Dark/Light Themes

### ✅ Pro Features (Freemium)
- [x] Parametric Equalizer
- [x] AI-Powered Stem Separation
- [x] Professional Mixer Interface
- [x] Advanced DSP Effects
- [x] Audio Export (WAV/FLAC)
- [x] Google Play Billing Integration

### ✅ Technical Features
- [x] Native C++ Audio Processing
- [x] Oboe Low-Latency Audio Engine
- [x] TensorFlow Lite ML Integration
- [x] Room Database for Presets
- [x] WorkManager Background Processing
- [x] Modular Architecture

## 🐛 Troubleshooting

### Common Issues

1. **SDK Location Not Found**
   ```bash
   # Set ANDROID_HOME environment variable
   export ANDROID_HOME=/path/to/android/sdk
   
   # Or update local.properties
   sdk.dir=/path/to/android/sdk
   ```

2. **NDK Not Found**
   ```bash
   # Install NDK via Android Studio SDK Manager
   # Or set ANDROID_NDK_HOME
   export ANDROID_NDK_HOME=$ANDROID_HOME/ndk/25.2.9519653
   ```

3. **CMake Not Found**
   ```bash
   # Install CMake via Android Studio SDK Manager
   # Or set CMAKE_DIR in local.properties
   cmake.dir=/path/to/cmake
   ```

4. **Build Errors**
   ```bash
   # Clean and rebuild
   ./gradlew clean build
   
   # Check for specific errors
   ./gradlew build --stacktrace
   ```

### Performance Optimization

1. **Enable Gradle Caching**
   ```properties
   # In gradle.properties
   org.gradle.caching=true
   org.gradle.parallel=true
   ```

2. **Increase Memory for Native Builds**
   ```properties
   # In gradle.properties
   org.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=1g
   ```

3. **Enable Configuration Cache**
   ```properties
   # In gradle.properties
   org.gradle.configuration-cache=true
   ```

## 📊 Build Variants

### Debug Build
```bash
./gradlew assembleDebug
```
- Includes debug symbols
- Optimized for development
- Larger APK size

### Release Build
```bash
./gradlew assembleRelease
```
- Optimized for production
- Smaller APK size
- Requires signing configuration

### Bundle Build
```bash
./gradlew bundleRelease
```
- Android App Bundle format
- Optimized for Play Store
- Dynamic delivery support

## 🔐 Signing Configuration

For release builds, configure signing in `app/build.gradle.kts`:

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("keystore/release.keystore")
            storePassword = "your-store-password"
            keyAlias = "your-key-alias"
            keyPassword = "your-key-password"
        }
    }
    
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}
```

## 🚀 Deployment

### Google Play Store
1. Build release bundle: `./gradlew bundleRelease`
2. Upload to Google Play Console
3. Configure Pro features in Play Console
4. Set up in-app purchases

### Internal Testing
1. Build debug APK: `./gradlew assembleDebug`
2. Install on test devices
3. Test all features including Pro features

## 📈 Next Steps

1. **Add Real Audio Files**: Replace placeholder audio with actual files
2. **Implement File Picker**: Add proper file selection UI
3. **Add ML Models**: Download and integrate Spleeter models
4. **Test on Real Devices**: Verify performance and compatibility
5. **Add Analytics**: Implement usage tracking
6. **Optimize Performance**: Profile and optimize audio processing

---

**Audio Player Pro** - Professional audio processing on Android! 🎵