package com.example.audioplayer

import android.content.ContentUris
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.provider.MediaStore

data class AudioFile(
    val uri: Uri,
    val displayName: String,
    val id: Long,
    val artist: String,
    val duration: Int,
    val title: String
)

fun getAudioFiles(context: Context): List<AudioFile> {
    val audioList = mutableListOf<AudioFile>()

    val collection = MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
    val projection = arrayOf(
        MediaStore.Audio.Media._ID,
        MediaStore.Audio.Media.DISPLAY_NAME,
        MediaStore.Audio.Media.ARTIST,
        MediaStore.Audio.Media.DURATION,
        MediaStore.Audio.Media.TITLE
    )

    // Show only music that is at least 5 seconds long
    val selection = "${MediaStore.Audio.Media.IS_MUSIC} != 0 AND ${MediaStore.Audio.Media.DURATION} >= 5000"

    val query: Cursor? = context.contentResolver.query(
        collection,
        projection,
        selection,
        null,
        "${MediaStore.Audio.Media.TITLE} ASC"
    )

    query?.use { cursor ->
        val idColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
        val displayNameColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DISPLAY_NAME)
        val artistColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)
        val durationColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION)
        val titleColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)

        while (cursor.moveToNext()) {
            val id = cursor.getLong(idColumn)
            val displayName = cursor.getString(displayNameColumn)
            val artist = cursor.getString(artistColumn)
            val duration = cursor.getInt(durationColumn)
            val title = cursor.getString(titleColumn)

            val contentUri: Uri = ContentUris.withAppendedId(
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                id
            )

            audioList.add(AudioFile(contentUri, displayName, id, artist, duration, title))
        }
    }

    return audioList
}
