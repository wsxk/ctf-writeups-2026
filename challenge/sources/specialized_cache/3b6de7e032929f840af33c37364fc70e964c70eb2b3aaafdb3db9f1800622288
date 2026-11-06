package com.bsidessf.vinyldrop

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.firebase.functions.FirebaseFunctions

class WelcomeActivity : AppCompatActivity() {
    private val functions by lazy { FirebaseFunctions.getInstance() }

    private val scanLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            if (result.resultCode == Activity.RESULT_OK) {
                val value = result.data?.getStringExtra(BarcodeScanActivity.EXTRA_BARCODE_VALUE)

                if (!value.isNullOrBlank()) {
                    // ✅ You now have the scanned QR content
                    sendScanToFunction(value)
                } else {
                    Toast.makeText(this, "No QR content found", Toast.LENGTH_SHORT).show()
                }
            } else {
                // User backed out or scan didn't complete
                Toast.makeText(this, "Scan cancelled", Toast.LENGTH_SHORT).show()
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_welcome)

        val scanButton = findViewById<MaterialButton>(R.id.scanBarcodeButton)
        scanButton.setOnClickListener { startBarcodeScan() }
    }

    private fun startBarcodeScan() {
        val intent = Intent(this, BarcodeScanActivity::class.java)
        scanLauncher.launch(intent)
    }

    private fun sendScanToFunction(value: String) {
        val data = hashMapOf("value" to value)
        functions
            .getHttpsCallable("validateScanPayload")
            .call(data)
            .addOnSuccessListener { result ->
                val payload = result.data as? Map<*, *>
                val success = payload?.get("success") as? Boolean ?: false
                val reward = payload?.get("reward") as? String
                val isError = payload?.get("error") as? Boolean ?: false
                val reason = payload?.get("reason") as? String

                when {
                    success && !reward.isNullOrBlank() -> {
                        val intent = Intent(this, RewardActivity::class.java)
                            .putExtra(RewardActivity.EXTRA_REWARD_VALUE, reward)
                        startActivity(intent)
                    }
                    isError -> {
                        Log.e("WelcomeActivity", "Scan rejected: $reason")
                        val intent = Intent(this, RewardActivity::class.java)
                            .putExtra(RewardActivity.EXTRA_REWARD_VALUE, reason ?: "Scan rejected")
                            .putExtra(RewardActivity.EXTRA_IS_ERROR, true)
                        startActivity(intent)
                    }
                    else -> {
                        Toast.makeText(this, "Scan accepted", Toast.LENGTH_SHORT).show()
                    }
                }
            }
            .addOnFailureListener { e ->
                Log.e("WelcomeActivity", "Scan rejected", e)
                val intent = Intent(this, RewardActivity::class.java)
                    .putExtra(
                        RewardActivity.EXTRA_REWARD_VALUE,
                        e.localizedMessage ?: "Scan rejected"
                    )
                    .putExtra(RewardActivity.EXTRA_IS_ERROR, true)
                startActivity(intent)
            }
    }
}
