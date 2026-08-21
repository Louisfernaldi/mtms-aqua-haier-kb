(function (root) {
  "use strict";

  function create() {
    var saveBusy = false;
    var saveSequence = 0;

    return {
      begin: function () {
        if (saveBusy) return 0;
        saveBusy = true;
        saveSequence += 1;
        return saveSequence;
      },
      isCurrent: function (sequence) {
        return saveBusy && sequence === saveSequence;
      },
      finish: function (sequence) {
        if (!this.isCurrent(sequence)) return false;
        saveBusy = false;
        return true;
      },
      invalidate: function () {
        saveSequence += 1;
        saveBusy = false;
        return saveSequence;
      },
      state: function () {
        return { busy: saveBusy, sequence: saveSequence };
      },
    };
  }

  root.MTMSCompetitorSaveLock = { create: create };
})(typeof window !== "undefined" ? window : globalThis);
