with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        // TOP tabs: Detail / Perbandingan (specs)
        var modalBox = document.querySelector(".pk-modal-box");
        var tabBtns = modalBox.querySelectorAll(".pk-modal-tab");
        var tabPanels = modalBox.querySelectorAll(".pk-modal-tabpanel");
        var compLoaded = false;
        tabBtns.forEach(function (btn) {
          btn.onclick = function () {
            var tab = this.getAttribute("data-tab");
            tabBtns.forEach(function (b) { b.classList.remove("active"); });
            tabPanels.forEach(function (p) { p.style.display = "none"; });
            this.classList.add("active");
            modalBox.querySelector('.pk-modal-tabpanel[data-tab="' + tab + '"]').style.display = "block";
            if (tab === "comparison") modalBox.classList.add("pk-modal-wide");
            else modalBox.classList.remove("pk-modal-wide");
            if (tab === "comparison" && !compLoaded) {
              compLoaded = true;
              var compPanel = modalBox.querySelector('.pk-modal-tabpanel[data-tab="comparison"]');
              loadCompetitorData().then(function () {
                var competitors = buildCompetitorFilmstrip(p);
                if (competitors) {
                  compPanel.innerHTML = renderFilmstrip(competitors, "-top");
                  initFilmstrip(competitors, "-top");
                } else {
                  compPanel.innerHTML = '<p class="pk-benefit">Tidak ada data perbandingan untuk kategori ini.</p>';
                }
              });
            }
          };
        });

        // FOOTER tabs: Foto Produk / Perbandingan (images + filmstrip)
        var footerTabBtns = modalBox.querySelectorAll(".pk-modal-footer-tab");
        var footerPanels = modalBox.querySelectorAll(".pk-modal-footer-panel");
        var footerCompLoaded = false;
        footerTabBtns.forEach(function (btn) {
          btn.onclick = function () {
            var tab = this.getAttribute("data-footer");
            footerTabBtns.forEach(function (b) { b.classList.remove("active"); });
            footerPanels.forEach(function (p) { p.style.display = "none"; });
            this.classList.add("active");
            modalBox.querySelector('.pk-modal-footer-panel[data-footer="' + tab + '"]').style.display = "block";
            if (tab === "comparison" && !footerCompLoaded) {
              footerCompLoaded = true;
              var compPanel = modalBox.querySelector('.pk-modal-footer-panel[data-footer="comparison"]');
              loadCompetitorData().then(function () {
                var competitors = buildCompetitorFilmstrip(p);
                if (competitors) {
                  compPanel.innerHTML = renderFilmstrip(competitors, "-footer");
                  initFilmstrip(competitors, "-footer");
                } else {
                  compPanel.innerHTML = '<p class="pk-benefit">Tidak ada data perbandingan untuk kategori ini.</p>';
                }
              });
            }
          };
        });

        // Init photo gallery in footer
        var gal = modalBox.querySelector(".pk-gal");
        if (gal) {
          var galImg = gal.querySelector(".pk-gal-img");
          var thumbBtns = gal.querySelectorAll(".pk-gal-thumb");
          function setFoto(i) {
            i = (i + fotos.length) % fotos.length;
            galImg.src = fotos[i];
            galImg.setAttribute("data-idx", i);
            for (var k = 0; k < thumbBtns.length; k++) {
              if (Number(thumbBtns[k].getAttribute("data-idx")) === i) {
                thumbBtns[k].classList.add("active");
              } else {
                thumbBtns[k].classList.remove("active");
              }
            }
          }
          var navs = gal.querySelectorAll(".pk-gal-nav");
          for (var j = 0; j < navs.length; j++) {
            navs[j].onclick = function () {
              setFoto(Number(galImg.getAttribute("data-idx")) + Number(this.getAttribute("data-dir")));
            };
          }
          for (var t = 0; t < thumbBtns.length; t++) {
            thumbBtns[t].onclick = function () {
              setFoto(Number(this.getAttribute("data-idx"));
            };
          }
        }

        var modalEl = document.querySelector(".pk-modal");
        if (modalEl) modalEl.classList.add("open");
        document.body.style.overflow = "hidden";
      }"""

new = """}

        var modalEl = document.querySelector(".pk-modal");
        if (modalEl) modalEl.classList.add("open");
        document.body.style.overflow = "hidden";
      }"""

if old in content:
    content = content.replace(old, new)
    with open('site/js/produk.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('OLD NOT FOUND')
    idx = content.find('TOP tabs')
    if idx >= 0:
        print('Found at', idx)