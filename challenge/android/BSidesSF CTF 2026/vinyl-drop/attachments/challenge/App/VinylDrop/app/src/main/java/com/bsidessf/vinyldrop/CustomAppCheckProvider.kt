package com.bsidessf.vinyldrop

import android.net.Uri
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.TaskCompletionSource
import com.google.firebase.appcheck.AppCheckProvider
import com.google.firebase.appcheck.AppCheckToken
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.FirebaseApp
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class CustomAppCheckProvider(private val app: FirebaseApp) : AppCheckProvider {
    private val executor = Executors.newSingleThreadExecutor()

    override fun getToken(): Task<AppCheckToken> {
        val tcs = TaskCompletionSource<AppCheckToken>()
        val auth = FirebaseAuth.getInstance(app)
        val user = auth.currentUser
        if (user == null) {
            tcs.setException(IllegalStateException("User must be signed in to mint App Check token."))
            return tcs.task
        }

        user.getIdToken(false)
            .addOnSuccessListener { result ->
                val idToken = result.token
                if (idToken.isNullOrBlank()) {
                    tcs.setException(IllegalStateException("Failed to fetch ID token."))
                    return@addOnSuccessListener
                }
                executor.execute {
                    try {
                        val tokenResponse = mintToken(idToken)
                        tcs.setResult(tokenResponse)
                    } catch (e: Exception) {
                        tcs.setException(e)
                    }
                }
            }
            .addOnFailureListener { e ->
                tcs.setException(e)
            }

        return tcs.task
    }

    private fun mintToken(idToken: String): AppCheckToken {
        val url = URL(buildMintUrl())
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Authorization", "Bearer $idToken")
            doOutput = true
        }

        val body = JSONObject()
            .put("appId", app.options.applicationId)
            .toString()
            .toByteArray(Charsets.UTF_8)

        connection.outputStream.use { it.write(body) }

        val responseCode = connection.responseCode
        val responseStream = if (responseCode in 200..299) {
            connection.inputStream
        } else {
            connection.errorStream
        }
        val responseBody = responseStream?.bufferedReader()?.use { it.readText() } ?: ""

        if (responseCode !in 200..299) {
            throw IOException("App Check mint failed ($responseCode): $responseBody")
        }

        val json = JSONObject(responseBody)
        val token = json.getString("token")
        val ttlMillis = json.optLong("ttlMillis", 60 * 60 * 1000L)
        val expireAt = System.currentTimeMillis() + ttlMillis

        return object : AppCheckToken() {
            override fun getToken(): String = token
            override fun getExpireTimeMillis(): Long = expireAt
        }
    }

    private fun buildMintUrl(): String {
        val projectId = app.options.projectId ?: "vinyldrop-corgi"
        return Uri.Builder()
            .scheme("https")
            .authority("us-central1-$projectId.cloudfunctions.net")
            .appendPath("mintAppCheckToken")
            .build()
            .toString()
    }
}
