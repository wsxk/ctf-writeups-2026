package com.bsidessf.vinyldrop

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class RewardActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_reward)

        val rewardText = findViewById<TextView>(R.id.rewardText)
        val rewardTitle = findViewById<TextView>(R.id.rewardTitle)
        val isError = intent.getBooleanExtra(EXTRA_IS_ERROR, false)
        val value = intent.getStringExtra(EXTRA_REWARD_VALUE) ?: ""

        if (isError) {
            rewardTitle.text = getString(R.string.reward_error_title)
            rewardText.setTextColor(
                ContextCompat.getColor(this, android.R.color.holo_red_dark)
            )
        } else {
            rewardTitle.text = getString(R.string.reward_congrats)
        }
        rewardText.text = value
    }

    companion object {
        const val EXTRA_REWARD_VALUE = "extra_reward_value"
        const val EXTRA_IS_ERROR = "extra_is_error"
    }
}
