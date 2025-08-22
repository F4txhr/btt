package com.audioplayerpro.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import com.audioplayerpro.MainActivity
import com.audioplayerpro.R
import com.audioplayerpro.viewmodel.MainViewModel

class AudioPlaybackService : MediaSessionService() {
    
    private lateinit var mediaSession: MediaSession
    private lateinit var player: ExoPlayer
    private lateinit var notificationManager: NotificationManager
    
    companion object {
        const val NOTIFICATION_ID = 1001
        const val CHANNEL_ID = "audio_playback_channel"
    }
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize ExoPlayer
        player = ExoPlayer.Builder(this).build()
        
        // Initialize MediaSession
        mediaSession = MediaSession.Builder(this, player).build()
        
        // Initialize notification manager
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        // Create notification channel
        createNotificationChannel()
        
        // Set up player listeners
        setupPlayerListeners()
    }
    
    private fun setupPlayerListeners() {
        player.addListener(object : Player.Listener {
            override fun onPlaybackStateChanged(playbackState: Int) {
                updateNotification()
            }
            
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                updateNotification()
            }
        })
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Audio Playback",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Audio playback controls"
                setShowBadge(false)
            }
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun updateNotification() {
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
    }
    
    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val playPauseIcon = if (player.isPlaying) {
            R.drawable.ic_pause
        } else {
            R.drawable.ic_play
        }
        
        val playPauseAction = NotificationCompat.Action(
            playPauseIcon,
            if (player.isPlaying) "Pause" else "Play",
            MediaSession.Callback.createMediaButtonPendingIntent(
                this,
                if (player.isPlaying) androidx.media3.session.SessionCommand.COMMAND_CODE_PLAYER_PAUSE
                else androidx.media3.session.SessionCommand.COMMAND_CODE_PLAYER_PLAY
            )
        )
        
        val previousAction = NotificationCompat.Action(
            R.drawable.ic_previous,
            "Previous",
            MediaSession.Callback.createMediaButtonPendingIntent(
                this,
                androidx.media3.session.SessionCommand.COMMAND_CODE_PLAYER_PREVIOUS
            )
        )
        
        val nextAction = NotificationCompat.Action(
            R.drawable.ic_next,
            "Next",
            MediaSession.Callback.createMediaButtonPendingIntent(
                this,
                androidx.media3.session.SessionCommand.COMMAND_CODE_PLAYER_NEXT
            )
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Audio Player Pro")
            .setContentText("Now Playing")
            .setSmallIcon(R.drawable.ic_music_note)
            .setContentIntent(pendingIntent)
            .addAction(previousAction)
            .addAction(playPauseAction)
            .addAction(nextAction)
            .setStyle(
                androidx.media.app.NotificationCompat.MediaStyle()
                    .setMediaSession(mediaSession.sessionCompatToken)
                    .setShowActionsInCompactView(0, 1, 2)
            )
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }
    
    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? {
        return mediaSession
    }
    
    override fun onDestroy() {
        mediaSession.release()
        player.release()
        super.onDestroy()
    }
    
    // Public methods for controlling playback
    fun playAudioFile(filePath: String) {
        val mediaItem = MediaItem.fromUri(filePath)
        player.setMediaItem(mediaItem)
        player.prepare()
        player.play()
    }
    
    fun pause() {
        player.pause()
    }
    
    fun resume() {
        player.play()
    }
    
    fun stop() {
        player.stop()
    }
    
    fun seekTo(position: Long) {
        player.seekTo(position)
    }
    
    fun setVolume(volume: Float) {
        player.volume = volume
    }
    
    fun getCurrentPosition(): Long = player.currentPosition
    
    fun getDuration(): Long = player.duration
    
    fun isPlaying(): Boolean = player.isPlaying
}