package com.bsidessf.vinyldrop

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import android.widget.Toast
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.google.firebase.auth.FirebaseAuth

class RegisterActivity : AppCompatActivity() {

    private lateinit var auth: FirebaseAuth

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_register)

        auth = FirebaseAuth.getInstance()

        val emailInput = findViewById<TextInputEditText>(R.id.registerEmailInput)
        val passwordInput = findViewById<TextInputEditText>(R.id.registerPasswordInput)
        val confirmPasswordInput =
            findViewById<TextInputEditText>(R.id.registerConfirmPasswordInput)
        val registerButton = findViewById<MaterialButton>(R.id.registerButton)

        registerButton.setOnClickListener {
            val email = emailInput.text?.toString()?.trim() ?: ""
            val password = passwordInput.text?.toString() ?: ""
            val confirmPassword = confirmPasswordInput.text?.toString() ?: ""

            if (!isValid(email, password, confirmPassword)) {
                return@setOnClickListener
            }

            createAccount(email, password)
        }
    }

    private fun isValid(
        email: String,
        password: String,
        confirmPassword: String
    ): Boolean {
        if (email.isEmpty()) {
            toast("Email is required")
            return false
        }

        if (password.length < 6) {
            toast("Password must be at least 6 characters")
            return false
        }

        if (password != confirmPassword) {
            toast("Passwords do not match")
            return false
        }

        return true
    }

    private fun createAccount(email: String, password: String) {
        auth.createUserWithEmailAndPassword(email, password)
            .addOnCompleteListener(this) { task ->
                if (task.isSuccessful) {
                    toast("Account created successfully")
                    finish() // return to login screen
                } else {
                    toast(task.exception?.localizedMessage ?: "Registration failed")
                }
            }
    }

    private fun toast(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }
}

