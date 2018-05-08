
/*页面详情中的编辑*/
$(document).ready(function() {	
	
	/*$(".editInput").editable({
		type:"select",
		submit:"OK",
		cssclass : "editable"
	});*/
	
	/*子网和网络映射显示*/
	$(".subnet-info").popover();
	
	 //Multiselect - Select2 plug-in
	$("#subnet-vm").val(["虚拟机1","虚拟机3"]).select2();
	$("#ip-pond").val(["IP1","IP3"]).select2();
	
	
	$(".remove-subnet").click(function () {
		$(this).parent().parent().addClass('animated fadeOut');
		$(this).parent().parent().attr('id', 'id_a');
		//$(this).parent().parent().parent().hide();
		setTimeout(function () {
		$('#id_a').remove();
		}, 400);
		return false;
		}); 
	
});

//Input mask - Input helper
$(function($){
	 $("#tin").mask("999.999.999.999");
});
