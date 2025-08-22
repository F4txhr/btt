#include <jni.h>
#include <string>
#include <oboe/Oboe.h>

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_audioplayer_core_NativeLib_stringFromJNI(
        JNIEnv* env,
        jobject /* this */) {

    // Create a dummy audio stream builder to verify Oboe linkage.
    // This code doesn't actually open a stream, but it uses the Oboe library,
    // which is enough to confirm that the project is linking correctly.
    oboe::AudioStreamBuilder builder;
    builder.setDirection(oboe::Direction::Output);
    builder.setPerformanceMode(oboe::PerformanceMode::LowLatency);
    builder.setSharingMode(oboe::SharingMode::Exclusive);

    std::string hello = "Hello from C++ with Oboe linked!";
    return env->NewStringUTF(hello.c_str());
}
