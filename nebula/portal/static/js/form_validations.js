$(document).ready(function() {
	
	jQuery.extend(jQuery.validator.messages, {
        required: "必填字段",
		  remote: "请修正该字段",
		  email: "请输入正确格式的电子邮件",
		  url: "请输入合法的网址",
		  date: "请输入合法的日期",
		  dateISO: "请输入合法的日期 (ISO).",
		  number: "请输入合法的数字",
		  digits: "只能输入整数",
		  creditcard: "请输入合法的信用卡号",
		  equalTo: "请再次输入相同的值",
		  accept: "请输入拥有合法后缀名的字符串",
		  maxlength: jQuery.validator.format("请输入一个 长度最多是 {0} 的字符串"),
		  minlength: jQuery.validator.format("请输入一个 长度最少是 {0} 的字符串"),
		  rangelength: jQuery.validator.format("请输入 一个长度介于 {0} 和 {1} 之间的字符串"),
		  range: jQuery.validator.format("请输入一个介于 {0} 和 {1} 之间的值"),
		  max: jQuery.validator.format("请输入一个最大为{0} 的值"),
		  min: jQuery.validator.format("请输入一个最小为{0} 的值")
		});
		
	//Traditional form validation sample
	//表单中input的验证
	$('#form_traditional_validation').validate({
                focusInvalid: false, 
                ignore: "",
                rules: {
                    formName: {
                        minlength: 2,
                        required: true
                    }
                },
                errorPlacement: function (label, element) { // render error placement for each input type   
					$('<span class="error"></span>').insertAfter(element).append(label)
                    var parent = $(element).parent('.input-validation');
                    parent.removeClass('success-control').addClass('error-control');  
                },

                highlight: function (element) { // hightlight error inputs
					var parent = $(element).parent();
                    parent.removeClass('success-control').addClass('error-control'); 
                },
                success: function (label, element) {
					var parent = $(element).parent('.input-validation');
					parent.removeClass('error-control').addClass('success-control'); 
                },
				messages: {
				   formName:{ 
						 required: "请输入名称",
						 minlength: "名称不能少于2个字符"
				   }
				}
            });	
			
	//Input mask - Input helper
	//输入框内容控制
   $("#ip").mask("999.999.999.999");
	
	//更改配置-虚拟机slider
	$('.slider-1').slider().on("slide",function(e){
		$("#sliderValue-1").val(e.value );
	});	
	$('.slider-2').slider().on("slide",function(e){
		$("#sliderValue-2").val(e.value );
	});	
	
	//高级设置中的显示和隐藏
	$(".advanceSetting-1").click(function(){
		$(".advanceSettingInfo-1").fadeToggle();
		});
	$(".advanceSetting-2").click(function(){
		$(".advanceSettingInfo-2").fadeToggle();
		});
	$(".advanceSetting-3").click(function(){
		$(".advanceSettingInfo-3").fadeToggle();
		});
	$(".advanceSetting-4").click(function(){
		$(".advanceSettingInfo-4").fadeToggle();
		});
	$(".addRouter").click(function(){
		$(".addRouterInfo").fadeToggle();
		});
	$(".addIP-1").click(function(){
		$(".addIPInfo").show();
		});
	$(".deleteIP").click(function(){
		$(this).parent().parent().parent().hide();
		});
	
	//radio选中为yes
	$("#yes").click(function(){
		$(".radio-info").show();
		});
	$("#no").click(function(){
		$(".radio-info").hide();
		});
		
	//弹出框的问好说明信息
	$(".formNameInfo").tooltip('toggle');
	$(".formNameInfo").tooltip('hide');
	
	//Form Wizard Validations
	//新建虚拟机
	var $validator = $("#commentForm").validate({
		  rules: {
		    txtFullName: {
		      required: true,
		      minlength: 3
		    }
		  },
		  errorPlacement: function(label, element) {
				$('<span class="arrow"></span>').insertBefore(element);
				$('<span class="error"></span>').insertAfter(element).append(label)
			}
		});

	/*$('#rootwizard-1').bootstrapWizard({
	  		'tabClass': 'form-wizard',
	  		'onNext': function(tab, navigation, index) {
	  			var $valid = $("#commentForm").valid();
	  			if(!$valid) {
	  				$validator.focusInvalid();
	  				return false;
	  			}
				else{
					$('#rootwizard').find('.form-wizard').children('li').eq(index-1).addClass('complete');
					$('#rootwizard').find('.form-wizard').children('li').eq(index-1).find('.step').html('<i class="icon-ok"></i>');	
				}
	  		}
	 });	*/
	
	$('#rootwizard').bootstrapWizard({
		'onNext': function(tab, navigation, index) {
				if($(".nav-tabs li:eq(-2)").hasClass("active")){
					$('#wizard_next').attr('style','display:none');
					$('#wizard_last').removeAttr('style');
					}
	  		},
			 'onPrevious': function(tab, navigation, index) {
				 if($(".nav-tabs li:eq(-1)").hasClass("active")){
					$('#wizard_next').removeAttr('style');
					$('#wizard_last').attr('style','display:none');
					}
				} 
		});
	
	$(".cpu-check").click(function(){
		$(".cpu-check").removeClass("btn-success");
		$(".cpu-check").addClass("btn-white");
		$(this).removeClass("btn-white");
		$(this).addClass("btn-success");
		});
	$(".memory-check").click(function(){
		$(".memory-check").removeClass("btn-success");
		$(".memory-check").addClass("btn-white");
		$(this).removeClass("btn-white");
		$(this).addClass("btn-success");
		});
});


