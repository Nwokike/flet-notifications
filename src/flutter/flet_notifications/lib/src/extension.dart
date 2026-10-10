import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

class Extension extends FletExtension {
  @override
  void ensureInitialized() {
    // Plugin initialization is driven by the LocalNotifications service
    // control, which carries the per-app settings. Nothing happens here.
  }

  @override
  FletService? createService(Control control) {
    switch (control.type) {
      default:
        return null;
    }
  }

  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      default:
        return null;
    }
  }
}
