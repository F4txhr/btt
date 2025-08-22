package com.example.audioplayer

import android.Manifest
import android.content.ComponentName
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.media3.common.MediaItem
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import com.google.common.util.concurrent.ListenableFuture
import java.util.concurrent.Executors

@OptIn(ExperimentalPermissionsApi::class)
class MainActivity : ComponentActivity() {

    private var controllerFuture: ListenableFuture<MediaController>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AudioPlayerProTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    val permissionState = rememberPermissionState(
                        permission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            Manifest.permission.READ_MEDIA_AUDIO
                        } else {
                            Manifest.permission.READ_EXTERNAL_STORAGE
                        }
                    )

                    if (permissionState.status.isGranted) {
                        val controller = controllerFuture?.let { if (it.isDone) it.get() else null }
                        AudioPlayerScreen(controller)
                    } else {
                        PermissionRequestScreen { permissionState.launchPermissionRequest() }
                    }
                }
            }
        }
    }

    override fun onStart() {
        super.onStart()
        val sessionToken = SessionToken(this, ComponentName(this, PlaybackService::class.java))
        controllerFuture = MediaController.Builder(this, sessionToken).buildAsync()
    }

    override fun onStop() {
        controllerFuture?.let {
            MediaController.releaseFuture(it)
        }
        super.onStop()
    }
}

@Composable
fun PermissionRequestScreen(onGrantPermissionClick: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Permission needed to access audio files.")
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onGrantPermissionClick) {
            Text("Grant Permission")
        }
    }
}

@Composable
fun AudioPlayerScreen(controller: MediaController?) {
    val context = LocalContext.current
    var audioFiles by remember { mutableStateOf<List<AudioFile>>(emptyList()) }

    LaunchedEffect(Unit) {
        audioFiles = getAudioFiles(context)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Audio Player Pro") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.primary,
                )
            )
        }
    ) { padding ->
        LazyColumn(modifier = Modifier.padding(padding)) {
            items(audioFiles) { file ->
                AudioListItem(audioFile = file, onClick = {
                    controller?.setMediaItem(MediaItem.fromUri(file.uri))
                    controller?.prepare()
                    controller?.play()
                })
            }
        }
    }
}

@Composable
fun AudioListItem(audioFile: AudioFile, onClick: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Text(
            text = audioFile.title,
            style = MaterialTheme.typography.bodyLarge,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
        Text(
            text = audioFile.artist,
            style = MaterialTheme.typography.bodySmall,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
fun AudioPlayerProTheme(darkTheme: Boolean = true, content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (darkTheme) darkColorScheme() else lightColorScheme(),
        typography = MaterialTheme.typography,
        content = content
    )
}

@Composable
fun darkColorScheme() = darkColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFFBB86FC),
    primaryContainer = androidx.compose.ui.graphics.Color(0xFF3700B3),
    secondary = androidx.compose.ui.graphics.Color(0xFF03DAC6),
    background = androidx.compose.ui.graphics.Color(0xFF121212),
    surface = androidx.compose.ui.graphics.Color(0xFF121212),
    onPrimary = androidx.compose.ui.graphics.Color.Black,
    onSecondary = androidx.compose.ui.graphics.Color.Black,
    onBackground = androidx.compose.ui.graphics.Color.White,
    onSurface = androidx.compose.ui.graphics.Color.White,
)

@Composable
fun lightColorScheme() = lightColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF6200EE),
    primaryContainer = androidx.compose.ui.graphics.Color(0xFF3700B3),
    secondary = androidx.compose.ui.graphics.Color(0xFF03DAC6),
    background = androidx.compose.ui.graphics.Color.White,
    surface = androidx.compose.ui.graphics.Color.White,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    onSecondary = androidx.compose.ui.graphics.Color.Black,
    onBackground = androidx.compose.ui.graphics.Color.Black,
    onSurface = androidx.compose.ui.graphics.Color.Black,
)
