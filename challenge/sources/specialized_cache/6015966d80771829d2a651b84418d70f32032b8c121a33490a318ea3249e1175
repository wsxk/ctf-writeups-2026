package com.bsidessf.vinyldrop

import android.graphics.Bitmap
import androidx.camera.core.ImageProxy
import com.google.zxing.BarcodeFormat
import com.google.zxing.BinaryBitmap
import com.google.zxing.DecodeHintType
import com.google.zxing.LuminanceSource
import com.google.zxing.MultiFormatReader
import com.google.zxing.PlanarYUVLuminanceSource
import com.google.zxing.RGBLuminanceSource
import com.google.zxing.common.HybridBinarizer

object BarcodeDecoder {
    private val formats = listOf(
        BarcodeFormat.QR_CODE
    )

    private val hints = mapOf(
        DecodeHintType.POSSIBLE_FORMATS to formats
    )

    fun decodeFromImageProxy(imageProxy: ImageProxy): String? {
        val plane = imageProxy.planes[0]
        val buffer = plane.buffer
        val width = imageProxy.width
        val height = imageProxy.height
        val rowStride = plane.rowStride
        val pixelStride = plane.pixelStride

        val luminance = ByteArray(width * height)
        val rowData = ByteArray(rowStride)
        var offset = 0
        for (row in 0 until height) {
            buffer.position(row * rowStride)
            buffer.get(rowData, 0, rowStride)
            if (pixelStride == 1) {
                System.arraycopy(rowData, 0, luminance, offset, width)
                offset += width
            } else {
                for (col in 0 until width) {
                    luminance[offset++] = rowData[col * pixelStride]
                }
            }
        }

        val source = PlanarYUVLuminanceSource(
            luminance,
            width,
            height,
            0,
            0,
            width,
            height,
            false
        )
        return decodeWithRotation(source, imageProxy.imageInfo.rotationDegrees)
    }

    fun decodeFromBitmap(bitmap: Bitmap): String? {
        val width = bitmap.width
        val height = bitmap.height
        val pixels = IntArray(width * height)
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)
        val source = RGBLuminanceSource(width, height, pixels)
        return decodeWithRotation(source, 0)
    }

    private fun decodeWithRotation(source: LuminanceSource, rotationDegrees: Int): String? {
        var rotatedSource = source
        val normalizedRotation = ((rotationDegrees % 360) + 360) % 360
        val clockwiseRotations = normalizedRotation / 90
        val counterClockwiseRotations = (4 - clockwiseRotations) % 4
        repeat(counterClockwiseRotations) {
            if (rotatedSource.isRotateSupported) {
                rotatedSource = rotatedSource.rotateCounterClockwise()
            }
        }

        val reader = MultiFormatReader()
        reader.setHints(hints)
        val bitmap = BinaryBitmap(HybridBinarizer(rotatedSource))
        return try {
            reader.decodeWithState(bitmap).text
        } catch (_: Exception) {
            null
        } finally {
            reader.reset()
        }
    }
}
