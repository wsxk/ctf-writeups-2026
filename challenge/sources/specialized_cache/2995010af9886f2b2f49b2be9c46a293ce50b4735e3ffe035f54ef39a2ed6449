package com.bsidessf.vinyldrop

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.caverock.androidsvg.SVG
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class BarcodeScannerInstrumentedTest {

    @Test
    fun scanBarcodeFromExternalFilesDir() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val imageFile = File(context.getExternalFilesDir(null), "qr_code.svg")
        assertTrue("qr_code.svg not found at ${imageFile.absolutePath}", imageFile.exists())

        val baseBitmap = renderSvgToBitmap(imageFile)
        val targetHeight = 400
        val scaleFactor =
            if (baseBitmap.height >= targetHeight) 1 else (targetHeight / baseBitmap.height) + 1
        val scaledBitmap = if (scaleFactor == 1) {
            baseBitmap
        } else {
            Bitmap.createScaledBitmap(
                baseBitmap,
                baseBitmap.width * scaleFactor,
                baseBitmap.height * scaleFactor,
                false
            )
        }
        val paddedBitmap = addPadding(scaledBitmap, 50)
        val value = BarcodeDecoder.decodeFromBitmap(paddedBitmap)

        assertTrue("No QR code detected in ${imageFile.absolutePath}", !value.isNullOrBlank())
        Log.d("BarcodeScannerTest", "Scanned value: $value")
    }

    private fun renderSvgToBitmap(svgFile: File): Bitmap {
        svgFile.inputStream().use { stream ->
            val svg = SVG.getFromInputStream(stream)
            val width = if (svg.documentWidth > 0) {
                svg.documentWidth
            } else {
                svg.documentViewBox?.width() ?: 1024f
            }
            val height = if (svg.documentHeight > 0) {
                svg.documentHeight
            } else {
                svg.documentViewBox?.height() ?: 1024f
            }
            val bitmap = Bitmap.createBitmap(width.toInt(), height.toInt(), Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bitmap)
            canvas.drawColor(Color.WHITE)
            svg.renderToCanvas(canvas)
            return bitmap
        }
    }

    private fun addPadding(bitmap: Bitmap, padding: Int): Bitmap {
        val padded = Bitmap.createBitmap(
            bitmap.width + padding * 2,
            bitmap.height + padding * 2,
            Bitmap.Config.ARGB_8888
        )
        val canvas = Canvas(padded)
        canvas.drawColor(Color.WHITE)
        canvas.drawBitmap(bitmap, padding.toFloat(), padding.toFloat(), null)
        return padded
    }
}
