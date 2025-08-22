package com.audioplayerpro

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.audioplayerpro.ui.screens.*
import com.audioplayerpro.ui.theme.AudioPlayerProTheme
import com.audioplayerpro.viewmodel.MainViewModel

class MainActivity : ComponentActivity() {
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            // Permission granted, initialize audio
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Request storage permission
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.READ_EXTERNAL_STORAGE
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissionLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
        }

        setContent {
            AudioPlayerProTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AudioPlayerApp()
                }
            }
        }
    }
}

@Composable
fun AudioPlayerApp() {
    val navController = rememberNavController()
    val mainViewModel: MainViewModel = viewModel()
    val context = LocalContext.current

    // Initialize audio engine
    LaunchedEffect(Unit) {
        mainViewModel.initializeAudioEngine()
    }

    // Cleanup on dispose
    DisposableEffect(Unit) {
        onDispose {
            mainViewModel.cleanup()
        }
    }

    NavHost(navController = navController, startDestination = "player") {
        composable("player") {
            PlayerScreen(
                viewModel = mainViewModel,
                onNavigateToEqualizer = { navController.navigate("equalizer") },
                onNavigateToVisualizer = { navController.navigate("visualizer") },
                onNavigateToMixer = { navController.navigate("mixer") },
                onNavigateToSettings = { navController.navigate("settings") }
            )
        }
        
        composable("equalizer") {
            EqualizerScreen(
                viewModel = mainViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable("visualizer") {
            VisualizerScreen(
                viewModel = mainViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable("mixer") {
            MixerScreen(
                viewModel = mainViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable("settings") {
            SettingsScreen(
                viewModel = mainViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}