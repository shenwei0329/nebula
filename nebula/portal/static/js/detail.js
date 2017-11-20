function createMenu(){//资源右上角
	var $asyncMenu=$("div.tools .dropdown-menu a[data-url]");
	
	//异步请求操作弹出的菜单
	var id = $(".table-detail").find("tr td:first:contains(ID) ~ td ").text();
 	$asyncMenu.off("click").on("click",function(evt){
 		evt.preventDefault();
 		if($(this).parent().hasClass("disabled")){
			return;
		}
		var url= new String($(this).attr("data-url")).replace(/{id}/, id);
		var rule=$(this).attr("data-rule");
		createDynamicDivAjax(url,rule,0);
	 });
	
 	var name = $(".table-detail").find("tr td:contains(名称) ~ td ").text();
 	createLocalMenu( id , name ) ;
}

function createLocalMenu( id , resource_name ){
	var $localMenu = $("div.tools .dropdown-menu a[name]:not([data-url])");
 	$localMenu.off("click").on("click",function(evt){
 		evt.preventDefault();
		if($(this).parents("li").hasClass("disabled")){
			return;
		}
		var $target=$($(this).attr("name"));		
		showLocalMenu(id , resource_name ,$target[0]);
	});
}


function createListLeft(url){
	var date=new Date().getTime();
	$(".listleft").load(url+"&"+date,function(){
		$('.listleft').find('.reload').click(function (evt) {//a标签刷新
			evt.preventDefault();
			 createListLeft(url);
		});
		$(".listleft .nextpage a").click(function(evt){
			evt.preventDefault();
			//详情页(主要用来显示日志的 )列表翻页
			var page_url=($(this).attr("href")).replace(/(^\s*)|(\s*$)/g,"").split("?")[1];
			url = urlAddPagePara(url , page_url)
			createListLeft(url);
		});
	});
}

//做刷新先在div中添加class: reload_table
function createList(url , pDiv){
	var date=new Date().getTime();
	var reload_table ;
	if( pDiv == undefined){
		reload_table = $("div.reload_table") ;
	}else{
		reload_table = pDiv.find("div.reload_table");
	}
	
	reload_table.load(url+"&"+date,function(){
		reload_table.find('.reload').click(function (evt) {//a标签刷新
			evt.preventDefault();
			createList(url);
		});
		reload_table.find(".nextpage a").click(function(evt){
				evt.preventDefault();
				var url=($(this).attr("href")).replace(/(^\s*)|(\s*$)/g,"");
				
				createList(url , pDiv );
		});
	});
}

$(function(){
	if($(".others-info").length>0){
		var listlefturl=$(".listleft").attr("data-url");
		createListLeft(listlefturl);
	}
	$("a[name=a_load]").unbind("click").click(function(evt){
		evt.preventDefault();
		var url=$(this).attr("data-url");
		if(url&&url!=""){
			var pDiv = $(this).parents(".tab-pane");
			createList(url,pDiv);
		}
	});
	
	//按钮式刷新
	$("button.reload").off("click").on("click",function(evt){
		evt.preventDefault();
		var url=$(this).attr("data-url");
		if(url&&url!=""){
			createList(url);
		}
	});
	
	//按钮弹出菜单
	$("button[data-url]:not(.reload)").off("click").on("click",function(evt){
		evt.preventDefault();
		var url=$(this).attr("data-url");
		var rule=$(this).attr("data-rule");
		createDynamicDivAjax(url,rule,0);
	 });
	//给“更多”等操作弹出的菜单根据上级li样式绑定事件	按钮灰亮交由具体模块去控制
 	$(".btn-group .dropdown-menu a[data-url]").off("click").on("click",function(evt){
 		evt.preventDefault();
 		if($(this).parent().hasClass("disabled")){
			return;
		}
		var id= $("tbody input[type=checkbox]:checked").val();
		var url= new String($(this).attr("data-url")).replace(/{id}/, id);
		var rule=$(this).attr("data-rule");
		createDynamicDivAjax(url,rule,0);
	 });
 	
 	createMenu() ;
 	createMenuForCheck( $(".btn-group .dropdown-menu a[name]:not([data-url])") );
	
	$(".reload_table ").on("click",".nextpage a",function(evt){
		evt.preventDefault();
		var url=($(this).attr("href")).replace(/(^\s*)|(\s*$)/g,"");
		if(url&&url!=""){
			var pDiv = $(this).parents(".tab-pane");
			createList(url,pDiv);
		}
	});
});

