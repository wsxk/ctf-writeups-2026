// Invoke validateScanPayload("100+100+100") via Firebase Functions.
// Run after the user is signed in, otherwise App Check minting will fail.

Java.perform(function () {
  const FirebaseFunctions = Java.use("com.google.firebase.functions.FirebaseFunctions");
  const HashMap = Java.use("java.util.HashMap");
  function extractResultData(result) {
    // Try common access patterns for HttpsCallableResult data
    try {
      if (result.getData) {
        return result.getData();
      }
    } catch (e) {}
    try {
      if (result.data) {
        return result.data;
      }
    } catch (e) {}
    try {
      const cls = result.getClass();
      const field = cls.getDeclaredField("data");
      field.setAccessible(true);
      return field.get(result);
    } catch (e) {}
    return null;
  }

  const OnSuccessListener = Java.registerClass({
    name: "com.bsidessf.frida.ValidateSuccessListener",
    implements: [Java.use("com.google.android.gms.tasks.OnSuccessListener")],
    methods: {
      onSuccess: function (result) {
        try {
          const data = extractResultData(result);
          if (data !== null) {
            console.log("[validateScanPayload] success: " + data);
          } else {
            console.log("[validateScanPayload] success: " + result);
          }
        } catch (e) {
          console.log("[validateScanPayload] success, but failed to read data: " + e);
        }
      },
    },
  });

  const OnFailureListener = Java.registerClass({
    name: "com.bsidessf.frida.ValidateFailureListener",
    implements: [Java.use("com.google.android.gms.tasks.OnFailureListener")],
    methods: {
      onFailure: function (e) {
        console.log("[validateScanPayload] failure: " + e);
      },
    },
  });

  Java.scheduleOnMainThread(function () {
    try {
      const FirebaseAuth = Java.use("com.google.firebase.auth.FirebaseAuth");
      const auth = FirebaseAuth.getInstance();
      const user = auth.getCurrentUser();
      if (user === null) {
        console.log("[validateScanPayload] no signed-in user; open the app and login first");
        return;
      }
      const uid = user.getUid();
      const System = Java.use("java.lang.System");
      const unixMs = System.currentTimeMillis();
      const payload = uid + "+100+" + unixMs;
      console.log("[validateScanPayload] uid: " + uid);
      console.log("[validateScanPayload] unix_ms: " + unixMs);
      console.log("[validateScanPayload] payload: " + payload);
      const functions = FirebaseFunctions.getInstance();
      const data = HashMap.$new();
      data.put("value", payload);
      const task = functions.getHttpsCallable("validateScanPayload").call(data);
      task.addOnSuccessListener(OnSuccessListener.$new());
      task.addOnFailureListener(OnFailureListener.$new());
      console.log("[validateScanPayload] request sent");
    } catch (e) {
      console.log("[validateScanPayload] error sending request: " + e);
    }
  });
});
