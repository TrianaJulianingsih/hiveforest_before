// static/admin/js/order_item_autofill.js
(function($){
  // Debounce helper
  function debounce(fn, delay){
    let t = null;
    return function(...args){
      clearTimeout(t);
      t = setTimeout(()=>fn.apply(this, args), delay);
    };
  }

  // Hook a pair: code input -> select2 field
  function wirePair($code, $select){
    if (!$code.length || !$select.length) return;

    function ensureSelect2Ready(cb){
      if ($select.hasClass("select2-hidden-accessible")) return cb();
      // force init by opening once
      $select.one("select2:open", function(){ cb(); });
      try { $select.select2("open"); $select.select2("close"); } catch(e) {}
    }

    function searchAndPick(term){
      term = (term || "").trim();
      if (!term) return;

      ensureSelect2Ready(function(){
        // Open select2 & type into its search box
        try { $select.select2("open"); } catch(e) {}
        var $search = $(".select2-container--open .select2-search__field");
        if (!$search.length){ try { $select.select2("close"); } catch(e) {} return; }

        $search.val(term).trigger("input");

        // Wait for AJAX results, then choose the first enabled option
        setTimeout(function(){
          var $first = $(".select2-container--open .select2-results__option[role='option']").filter(function(){
            return !$(this).attr("aria-disabled");
          }).first();
          if ($first.length){
            $first.trigger("mouseup");
          }
          try { $select.select2("close"); } catch(e) {}
        }, 350);
      });
    }

    const debounced = debounce(function(){
      const v = $code.val();
      if (v && v.length >= 2) searchAndPick(v);
    }, 250);

    // Fire on typing/paste/blur/Enter
    $code.on("input", debounced);
    $code.on("paste", function(){ setTimeout(debounced, 0); });
    $code.on("blur", function(){ const v = ($code.val()||"").trim(); if (v) searchAndPick(v); });
    $code.on("keydown", function(e){
      if (e.key === "Enter"){
        e.preventDefault();
        const v = ($code.val()||"").trim();
        if (v) searchAndPick(v);
      }
    });
  }

  // Wire single form (non-inline)
  function wireSingleForm(){
    const $code = $("#id_items"); // your “items” text field
    const $select = $("#id_item"); // your FK field with autocomplete
    if ($code.length && $select.length){
      wirePair($code, $select);
    }
  }

  // Wire inline formsets too (handles dynamic add-row)
  function wireInlines(){
    // Pattern: id_form-0-items / id_form-0-item etc.
    $("[id$='-items']").each(function(){
      const codeId = this.id;
      const prefix = codeId.replace(/-items$/, "");
      const $code = $("#"+codeId);
      const $select = $("#"+prefix+"-item");
      wirePair($code, $select);
    });

    // When a new inline row is added, re-wire
    $(document).on("formset:added", function(_ev, $row){
      const $code = $row.find("[id$='-items']");
      const $select = $row.find("[id$='-item']");
      wirePair($code, $select);
    });
  }

  $(function(){
    wireSingleForm();
    wireInlines();
  });
})(django.jQuery);
