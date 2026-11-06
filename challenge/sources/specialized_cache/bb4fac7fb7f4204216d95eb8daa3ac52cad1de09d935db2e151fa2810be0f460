package com.bsidessf.doremi

import android.graphics.Color
import android.graphics.drawable.LayerDrawable
import android.os.Bundle
import android.view.View
import android.widget.ImageView
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.core.content.ContextCompat


class FrameActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_frame)
        val rightPitch = false

        val imageViewIds = listOf(
            R.id.imageOneCTF,
            R.id.imageTwoCTF,
            R.id.imageThreeCTF,
            R.id.imageFourCTF,
            R.id.imageFiveCTF
        )

        val drawableIds = listOf(
            R.drawable.aria_with_bg,
            R.drawable.sonnet_with_bg,
            R.drawable.cadence_with_bg,
            R.drawable.lyra_with_bg,
            R.drawable.tempo_with_bg
        )
        imageViewIds.zip(drawableIds).forEach { (viewId, drawableId) ->
            val iv = findViewById<ImageView>(viewId)
            iv.setImageResource(drawableId)
            val layer = iv.drawable as LayerDrawable
            val bg = layer.findDrawableByLayerId(R.id.bg)
            bg.setTint(Color.TRANSPARENT)
        }
        if (rightPitch) {
            findViewById<View>(R.id.rootLayout)
                .setBackgroundColor(ContextCompat.getColor(this, R.color.light_green))
        }
    }
}
