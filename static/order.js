
function ddselect(){
  var d = document.getElementById("inputGroupSelect01");
  var type = d.options[d.selectedIndex].text;
  var null_value = "NULL"
  if(type.localeCompare("MRKT") == 0 )
  {
    document.getElementById("price").value = null_value;
    document.getElementById("price").setAttribute('readonly', true);
  }

  if(type.localeCompare("LMT") == 0 )
  {
    document.getElementById("price").removeAttribute('readonly'); 
  }

}
