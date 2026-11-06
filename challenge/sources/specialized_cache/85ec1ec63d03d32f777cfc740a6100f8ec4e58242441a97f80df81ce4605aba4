package com.bsidessf.vinyldrop

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.Surface
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.OptIn
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class BarcodeScanActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_BARCODE_VALUE = "extra_barcode_value"
        private const val TAG = "BarcodeScanActivity"
    }

    private lateinit var previewView: PreviewView
    private lateinit var cameraExecutor: ExecutorService

    // Prevent double-firing when multiple frames detect the barcode
    @Volatile
    private var handledResult = false

    private val requestCameraPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) {
                startCamera()
            } else {
                toast("Camera permission is required to scan barcodes")
                finish()
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_barcode)

        previewView = findViewById(R.id.previewView)
        cameraExecutor = Executors.newSingleThreadExecutor()

        if (hasCameraPermission()) {
            startCamera()
        } else {
            requestCameraPermission.launch(Manifest.permission.CAMERA)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }

    private fun hasCameraPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder()
                .build()
                .also { it.setSurfaceProvider(previewView.surfaceProvider) }

            val options = BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                .build()

            val scanner = BarcodeScanning.getClient(options)

            val analysis = ImageAnalysis.Builder()
                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_YUV_420_888)
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor) { imageProxy ->
                        processImageProxy(scanner, imageProxy)
                    }
                }

            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            previewView.post {
                val rotation = previewView.display?.rotation ?: Surface.ROTATION_0
                preview.targetRotation = rotation
                analysis.targetRotation = rotation

                try {
                    cameraProvider.unbindAll()
                    cameraProvider.bindToLifecycle(
                        this,
                        cameraSelector,
                        preview,
                        analysis
                    )
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to bind camera use cases", e)
                    toast("Failed to start camera")
                    finish()
                }
            }
        }, ContextCompat.getMainExecutor(this))
    }

    @OptIn(ExperimentalGetImage::class)
    private fun processImageProxy(
        scanner: com.google.mlkit.vision.barcode.BarcodeScanner,
        imageProxy: ImageProxy
    ) {
        val mediaImage = imageProxy.image
        if (mediaImage == null) {
            imageProxy.close()
            return
        }

        val image = InputImage.fromMediaImage(
            mediaImage,
            imageProxy.imageInfo.rotationDegrees
        )

        scanner.process(image)
            .addOnSuccessListener { barcodes ->
                if (handledResult) return@addOnSuccessListener

                val value = pickBestBarcodeValue(barcodes)
                val fallbackValue =
                    if (value.isNullOrBlank()) BarcodeDecoder.decodeFromImageProxy(imageProxy) else value
                if (!fallbackValue.isNullOrBlank()) {
                    handledResult = true
                    returnResult(fallbackValue)
                }
            }
            .addOnFailureListener { e ->
                Log.e(TAG, "Barcode scan failed", e)
            }
            .addOnCompleteListener {
                // Important: close the frame so CameraX can continue
                imageProxy.close()
            }
    }

    private fun pickBestBarcodeValue(barcodes: List<Barcode>): String? {
        // Prefer rawValue (usually what you want), fall back to displayValue
        return barcodes.firstOrNull()?.rawValue ?: barcodes.firstOrNull()?.displayValue
    }

    private fun returnResult(value: String) {
        val data = Intent().putExtra(EXTRA_BARCODE_VALUE, value)
        setResult(Activity.RESULT_OK, data)
        finish()
    }

    private fun toast(message: String) {
        runOnUiThread {
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
        }
    }
}
