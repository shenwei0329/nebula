var _id="";
var _checkedbox="";
$(document).ready(function(){
	//***********************************BEGIN dropdown menu *****************************
	var loaction_url=location+"";
	if(loaction_url.indexOf("instance/instances")==-1
		&& loaction_url.indexOf("network/private-networks") <= 0	){
		$('.dropdown-toggle').click(function () {
			var len=$("input[type=checkbox]:checked").length;
			if(len<=0){
				$(".dropdown-menu li").attr("class","disabled");
			}else if(len>1){
				$(".dropdown-menu li").attr("class","disabled");
				//$(".dropdown-menu a[name*=delete]").parent().removeAttr("class");如果 要多选时打开
			}else{
				$(".dropdown-menu li").removeAttr("class");
				
				var status=	$("input[type=checkbox]:checked").parents("tr").find("td:eq(2)").text();
				if(status=="任务中"){
					$(".dropdown-menu li").attr("class","disabled");
				}else{
					$(".dropdown-menu li").removeAttr("class");
				}
			}
			$("img").trigger("unveil");
		});
	}
	
//***********************************END dropdown menu *****************************
		//Too Small for new file - Helps the to tick all options in the table
	$('tbody .checkbox input').live("click", function() {
			$(this).parents("tr").toggleClass('row_selected');
	});
	// Demo charts - not required
	$('.customer-sparkline').each(function () {
		$(this).sparkline('html', { type:$(this).attr("data-sparkline-type"), barColor:$(this).attr("data-sparkline-color") , enableTagOptions: true });
	});

	 //定义鼠标单击、双击事件和右键事件
	 var time = null;


	 //鼠标单击事件和右键事件--点击其他地方消失
	$("table tr.show-others td:not(':first-child')").bind("contextmenu", function(e){ return false; });
		/*$(".show-others").mousedown(function(e){
			//alert(e.which) // 1 = 鼠标左键 left; 2 = 鼠标中键; 3 = 鼠标右键
			return false;//阻止链接跳转
		});*/

		//表格中的资源使用情况
		$('.resource-list').tooltip('toggle');
		$('.resource-list').tooltip('hide');

		//操作日志内的具体时间显示
		$('.detail-time').tooltip('toggle');
		$('.detail-time').tooltip('hide');

		$('input[name=search]').keydown(function(e){//搜索
			if(e.keyCode==13){
				 search();
			}
		}); 
		
		$(".add-on").click(function(){//搜索
			 search();
		});
		$('button.reload').off("click").on("click",function(){
            reload( $(this) );
        });
		
		createMenu();
		showAjaxModal();
});

//创建本地弹出框
function createMenu(){
	var obj1=$(".dropdown-menu a").not("a[data-url]");
	var obj2=$(".rightMenu a");
	var $local_button = $("button[name]:not(.reload)")
	var loaction_url=location+"";
	
	clickEvent();
	createMenuForCheck(obj1);//本地弹出框	
	createMenuForCheck( $local_button );//本地弹出框	
	//rightMenuBind( obj2 );
}

function clickEvent(){
	 $("table tr.show-others").mousedown(function(e){
		 if(3 == e.which){	 //右键事件
			$("table tr.show-others").bind("contextmenu", function(){ return false; });
			$(".rightMenu").bind("contextmenu", function(){ return false; });
			var id=$(this).parent().find("input[type=checkbox]").val();
			var name=$(this).parent().find("td:eq(1)").text();
			var status=	$(this).parents("tr").find("td:eq(2)").text();
			if(status=="任务中"){
				$(".rightMenu li").addClass("disabled");
			}else{
				$(".rightMenu li").removeClass("disabled");
			}
			$(".rightMenu").attr("name",id+"$_&"+name);
			$(".rightMenu").show();//显示右键菜单
			$(".rightMenu").css("top",e.pageY);
			$(".rightMenu").css("left",e.pageX);
			try{
				rightMenuCtrl(this);
			}catch(e){
				console.log("没有定义右键菜单项控制函数，请检查具体模块");
			}
			e.stopPropagation();
         }else if(1 == e.which){//单击事件
					$("table tr ").removeClass('row_update');
					$("table tr ").removeClass('row_info');
					$(this).parent().addClass('row_info');
					var id=$(this).find("input[type=checkbox]").val();
					createDivRL(id);//生成下方左右div
              		setTimeout(function(){
					$(".others-info").fadeIn();
					e.stopPropagation();
				},300);

          }
       });

	//鼠标右键事件--点击其他地方消失
		$('.rightMenu').hover(function(e) {
			$(".rightMenu").unbind("mousedown");
		},function(){
			$('html').click(function(e) {
				$(".rightMenu").hide();
			});
		});
}



function createDivRL(param){//生成下方左右div
	var listlefturl=$(".listleft").attr("data-url");
	var listrighturl=$(".listright").attr("data-url");
	if($(".others-info").length>0){
		createListLeft(listlefturl+param);
		createListRight(listrighturl+param);
	}
	
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
				var page_url=($(this).attr("href")).replace(/(^\s*)|(\s*$)/g,"").split("?")[1];
				url = urlAddPagePara(url , page_url)
				createListLeft(url);
			});
	});
}

function createListRight(url){
	var date=new Date().getTime();
	$(".listright").load(url+"&"+date,function(){
		$('.listright').find('.reload').click(function (evt) {//a标签刷新
			evt.preventDefault();
			createListRight(url);
		});
		$(".listright .nextpage a").click(function(evt){
			evt.preventDefault();
			var page_url=($(this).attr("href")).replace(/(^\s*)|(\s*$)/g,"").split("?")[1];
			url = urlAddPagePara(url , page_url)
			createListRight(url);
		});
	});
}

function search(){
	$('input[name=search]').closest("form").submit();
}

function rightMenuBind( obj2 ){//右键菜单弹出框,暂未使用
	obj2.click(function(evt){
		evt.preventDefault();
		var target=$(this).attr("name");
		if($(this).parents("li").hasClass("disabled")){
			return;
		}
		if($(target)&&$(target).length>0){
			$(target+" input[name$=id]").val("");
			$(target+" form").resetform();
			var str=$(".rightMenu").attr("name");
			str=new String(str);
			var id="",name="";
			if(str!=null){
				var obj=str.split("$_&");
				if(obj.length>0){
					id=obj[0];
				}
				if(obj.length>1){
					name=obj[1];
				}
				if(new String(target).indexOf("delete")!=-1){
					$(target+" p").html("确定删除&nbsp;"+name+"&nbsp;?");
				}else{
					$(target+" .modal-header span").html(name);
				}
               
				$(target+" input[name$=id]").val(id);
				$(".rightMenu").hide();
				 $(target).find("button[type=submit]").removeAttr("disabled");
				 var url=new String( $(target+" form").attr("action"));
				 var old_url=$("input[name="+target+"_actionurl]");
				 if(old_url.length>0){
					 url=old_url.val();
				 }else{
					 $(target).append("<input type='hidden' name='" + target+ "_actionurl' value="+url+"/>"); 
				 }
				 url=url.replace(/{id}/, id).replace("\/\/","\/");
				 $(target+" form").attr("action",url);
				 $(target).modal("show");
			}
		}

	});
}
