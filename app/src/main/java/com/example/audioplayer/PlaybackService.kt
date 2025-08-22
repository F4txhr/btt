package com.example.audioplayer

import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService

class PlaybackService : MediaSessionService() {
    private var mediaSession: MediaSession? = null

    // Create your player and media session in the onCreate lifecycle event
    override fun onCreate() {
        super.onCreate()
        val player = ExoPlayer.Builder(this)
            .setAudioAttributes(AudioAttributes.DEFAULT, /* handleAudioFocus= */ true)
            .setHandleAudioBecomingNoisy(true)
            .setWakeMode(C.WAKE_MODE_LOCAL)
            .build()

        mediaSession = MediaSession.Builder(this, player).build()
    }

    // The user dismissed the notification. Stop the service.
    override fun onTaskRemoved(rootIntent: android.content.Intent?) {
        val player = mediaSession?.player
        if (player?.playWhenReady == false || player?.mediaItemCount == 0) {
            stopSelf()
        }
    }

    // Return a MediaSession to link with the MediaController that is making
    // this request.
    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? = mediaSession

    // Remember to release the player and session in onDestroy
    override fun onDestroy() {
        mediaSession?.run {
            player.release()
            release()
            mediaSession = null
        }
        super.onDestroy()
    }
}
