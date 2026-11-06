/* 
 * AI generated solution 
 * Frida hook for com.bsidessf.doremi.FrameActivity.
 * Since rightPitch is a local variable inside onCreate(), we can’t modify it
 * directly.  Instead, we hook the onCreate(Bundle) overload, invoke the original
 * implementation, and then force the same UI behaviour that would occur if
 * rightPitch were true.  All UI manipulation happens immediately on the UI thread.
 */
Java.perform(function() {
  try {
    var FrameActivity = Java.use('com.bsidessf.doremi.FrameActivity');
    var R_id = Java.use('com.bsidessf.doremi.R$id');
    var View = Java.use('android.view.View');

    // Get the correct onCreate(Bundle) overload
    var onCreateOrig = FrameActivity.onCreate.overload('android.os.Bundle');

    onCreateOrig.implementation = function(savedInstanceState) {
      // Call the original onCreate() so the Activity sets up normally
      var result = onCreateOrig.call(this, savedInstanceState);

      try {
        // Find the root layout by its resource ID
        var rootId = R_id.rootLayout.value;
        var rootObj = this.findViewById(rootId);
        if (rootObj) {
          // Cast to android.view.View to ensure setBackgroundColor exists
          var rootView = Java.cast(rootObj, View);
           rootView.setBackgroundColor.overload('int').call(rootView, 0xff8dc63f);
          console.log('rightPitch emulation: rootLayout background set to light green');
        } else {
          console.log('rightPitch emulation: rootLayout not found');
        }
      } catch (inner) {
        console.log('rightPitch emulation: error setting background: ' + inner);
      }

      return result;
    };
  } catch (err) {
    console.log('rightPitch emulation: failed to hook FrameActivity.onCreate: ' + err);
  }
});
