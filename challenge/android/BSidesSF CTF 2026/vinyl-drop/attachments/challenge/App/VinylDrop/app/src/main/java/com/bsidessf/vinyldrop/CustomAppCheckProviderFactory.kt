package com.bsidessf.vinyldrop

import com.google.firebase.FirebaseApp
import com.google.firebase.appcheck.AppCheckProvider
import com.google.firebase.appcheck.AppCheckProviderFactory

object CustomAppCheckProviderFactory : AppCheckProviderFactory {
    override fun create(app: FirebaseApp): AppCheckProvider {
        return CustomAppCheckProvider(app)
    }
}
