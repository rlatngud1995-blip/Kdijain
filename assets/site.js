(function () {
  // 헤더 구분선
  var top = document.getElementById('top');
  if (top) addEventListener('scroll', function () { top.classList.toggle('line', scrollY > 10); }, { passive: true });

  // 모바일 메뉴
  var nav = document.getElementById('nav'), tog = document.getElementById('navToggle');
  if (nav && tog) {
    tog.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      tog.setAttribute('aria-expanded', open);
      tog.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('open'); tog.setAttribute('aria-expanded', false); });
    });
  }

  // 시공사례 크게 보기
  var v = document.getElementById('viewer');
  if (v && v.showModal) {
    document.addEventListener('click', function (e) {
      var b = e.target.closest('.work button');
      if (!b) return;
      var img = document.getElementById('viewerImg');
      if (!img) { img = document.createElement('img'); img.id = 'viewerImg'; v.insertBefore(img, v.firstChild); }
      img.src = b.dataset.full; img.alt = b.querySelector('img').alt;
      document.getElementById('viewerCap').textContent = b.dataset.cap;
      v.showModal();
    });
    document.getElementById('viewerClose').addEventListener('click', function () { v.close(); });
    v.addEventListener('click', function (e) { if (e.target === v) v.close(); });
  }

  // 시공사례 분야 탭 + 더 보기 (메인)
  var grid = document.getElementById('worksGrid');
  if (grid) {
    var items = [].slice.call(grid.querySelectorAll('.work'));
    var more = document.getElementById('moreBtn');
    var filter = 'all', limit = 9;
    function render() {
      var shown = 0;
      items.forEach(function (it) {
        var match = filter === 'all' || it.dataset.c === filter;
        var visible = match && shown < limit;
        it.hidden = !visible;
        if (match) shown++;
      });
      var total = items.filter(function (it) { return filter === 'all' || it.dataset.c === filter; }).length;
      if (more) more.hidden = shown <= limit && total <= limit;
      if (more) more.hidden = total <= limit;
    }
    document.querySelectorAll('.tabs button').forEach(function (b) {
      b.addEventListener('click', function () {
        document.querySelectorAll('.tabs button').forEach(function (x) { x.setAttribute('aria-selected', x === b); });
        filter = b.dataset.f; limit = 9; render();
      });
    });
    if (more) more.addEventListener('click', function () { limit = 999; render(); });
    render();
  }
})();
