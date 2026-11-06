package com.bsidessf.vinyldrop

import android.app.Application
import com.google.firebase.FirebaseApp
import com.google.firebase.appcheck.FirebaseAppCheck

class VinylDropApp : Application() {
    override fun onCreate() {
        super.onCreate()
        FirebaseApp.initializeApp(this)
        val appCheck = FirebaseAppCheck.getInstance()
        appCheck.installAppCheckProviderFactory(AppCheckProviderFactoryProvider.provide())
        appCheck.setTokenAutoRefreshEnabled(true)
    }
}
