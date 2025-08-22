package com.audioplayerpro.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "eq_presets")
data class EQPreset(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val graphicEQGains: String, // JSON string of 10 float values
    val parametricBands: String, // JSON string of parametric bands
    val preampGain: Float = 1.0f,
    val limiterThreshold: Float = 0.95f,
    val limiterRatio: Float = 10.0f,
    val isPro: Boolean = false,
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "playlists")
data class Playlist(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val description: String = "",
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)

@Entity(
    tableName = "playlist_tracks",
    foreignKeys = [
        ForeignKey(
            entity = Playlist::class,
            parentColumns = ["id"],
            childColumns = ["playlistId"],
            onDelete = ForeignKey.CASCADE
        )
    ]
)
data class PlaylistTrack(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val playlistId: Long,
    val trackPath: String,
    val trackName: String,
    val artist: String = "",
    val duration: Long = 0,
    val position: Int = 0
)

@Entity(tableName = "audio_tracks")
data class AudioTrack(
    @PrimaryKey val path: String,
    val name: String,
    val artist: String = "",
    val album: String = "",
    val duration: Long = 0,
    val sampleRate: Int = 0,
    val bitDepth: Int = 0,
    val channels: Int = 2,
    val fileSize: Long = 0,
    val lastPlayed: Long = 0,
    val playCount: Int = 0
)

@Dao
interface EQPresetDao {
    @Query("SELECT * FROM eq_presets ORDER BY name ASC")
    fun getAllPresets(): Flow<List<EQPreset>>

    @Query("SELECT * FROM eq_presets WHERE isPro = 0 ORDER BY name ASC")
    fun getFreePresets(): Flow<List<EQPreset>>

    @Query("SELECT * FROM eq_presets WHERE isPro = 1 ORDER BY name ASC")
    fun getProPresets(): Flow<List<EQPreset>>

    @Insert
    suspend fun insertPreset(preset: EQPreset): Long

    @Update
    suspend fun updatePreset(preset: EQPreset)

    @Delete
    suspend fun deletePreset(preset: EQPreset)

    @Query("SELECT * FROM eq_presets WHERE id = :id")
    suspend fun getPresetById(id: Long): EQPreset?
}

@Dao
interface PlaylistDao {
    @Query("SELECT * FROM playlists ORDER BY updatedAt DESC")
    fun getAllPlaylists(): Flow<List<Playlist>>

    @Query("SELECT * FROM playlists WHERE id = :playlistId")
    suspend fun getPlaylistById(playlistId: Long): Playlist?

    @Insert
    suspend fun insertPlaylist(playlist: Playlist): Long

    @Update
    suspend fun updatePlaylist(playlist: Playlist)

    @Delete
    suspend fun deletePlaylist(playlist: Playlist)

    @Query("SELECT * FROM playlist_tracks WHERE playlistId = :playlistId ORDER BY position ASC")
    fun getTracksForPlaylist(playlistId: Long): Flow<List<PlaylistTrack>>

    @Insert
    suspend fun insertTrack(track: PlaylistTrack): Long

    @Delete
    suspend fun deleteTrack(track: PlaylistTrack)

    @Query("DELETE FROM playlist_tracks WHERE playlistId = :playlistId")
    suspend fun deleteAllTracksFromPlaylist(playlistId: Long)
}

@Dao
interface AudioTrackDao {
    @Query("SELECT * FROM audio_tracks ORDER BY lastPlayed DESC")
    fun getAllTracks(): Flow<List<AudioTrack>>

    @Query("SELECT * FROM audio_tracks WHERE name LIKE '%' || :query || '%' OR artist LIKE '%' || :query || '%'")
    fun searchTracks(query: String): Flow<List<AudioTrack>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTrack(track: AudioTrack)

    @Update
    suspend fun updateTrack(track: AudioTrack)

    @Delete
    suspend fun deleteTrack(track: AudioTrack)

    @Query("SELECT * FROM audio_tracks WHERE path = :path")
    suspend fun getTrackByPath(path: String): AudioTrack?

    @Query("UPDATE audio_tracks SET lastPlayed = :timestamp, playCount = playCount + 1 WHERE path = :path")
    suspend fun updatePlayStats(path: String, timestamp: Long = System.currentTimeMillis())
}

@Database(
    entities = [EQPreset::class, Playlist::class, PlaylistTrack::class, AudioTrack::class],
    version = 1
)
abstract class AudioDatabase : RoomDatabase() {
    abstract fun eqPresetDao(): EQPresetDao
    abstract fun playlistDao(): PlaylistDao
    abstract fun audioTrackDao(): AudioTrackDao

    companion object {
        @Volatile
        private var INSTANCE: AudioDatabase? = null

        fun getDatabase(context: android.content.Context): AudioDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AudioDatabase::class.java,
                    "audio_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}