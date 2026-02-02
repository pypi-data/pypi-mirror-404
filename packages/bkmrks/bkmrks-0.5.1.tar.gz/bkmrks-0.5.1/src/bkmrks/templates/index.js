/* index.js */
    function updateClock() {
      var d = new Date();
      var s = d.getSeconds().toString();
      var m = d.getMinutes().toString();
      var h = d.getHours().toString();

      document.getElementById("clock").innerHTML =
        (h).padStart(2,"0") +
        ":" +
        (m).padStart(2,"0") +
        ":" +
        (s).padStart(2,"0");
    }

    function updateMenu() {
      document.getElementById("menu_selected_{__catalog__}").style.display='inline';
    }


    function getItemWrapper(itemAlias){
      const wrapper = document.createElement("span")

      const wrapperLabel = document.createElement("span")
      wrapperLabel.setAttribute("class","bkmrks_item")
      wrapperLabel.setAttribute("class","bkmrks_item_label")
      wrapperLabel.innerText = itemAlias

      wrapper.appendChild(wrapperLabel)

      return wrapper
    }

    function appendElementInWrapper(innerElement, wrapper) {
      if (innerElement && innerElement.parentNode) {
        innerElement.parentNode.insertBefore(wrapper, innerElement);
        wrapper.appendChild(innerElement);
      }
    }

    function updateBkmrkItems(){
      var bkmrksItems = document.querySelectorAll("#bkmrks_items img")

      bkmrksItems.forEach((bkmrksItem) =>{
        const itemAlias = bkmrksItem.getAttribute("alt")
        const itemWrapper = getItemWrapper(itemAlias)
        appendElementInWrapper(bkmrksItem,itemWrapper)
      })
    }

    setInterval(updateClock, 1000);
    updateMenu();
    updateBkmrkItems()
