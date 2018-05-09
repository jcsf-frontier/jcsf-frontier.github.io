#! /usr/local/bin/perl
#
# akiary - Y.Akira's Diary CGI
#   Copyright (C) 2000-2005 by YAMAMOTO Akira
#   mailto:yakira at hi-ho.ne.jp
#   http://www.hi-ho.ne.jp/yakira/akiary/
#

# �o�[�W����
my $VERSION="0.61"; # 2005/03/29

# �p�����[�^���
my %FORM=&parse_param;

# akiary�ݒ�
my $akiary_cfg_file='cfg/akiary.cfg';
my $acfg=
  {
   user_cfg_file=>{''=>'cfg/user.cfg'},
   time_zone=>'+0900',
   newline => '<br>',
   charset => 'SHIFT_JIS',
  };
&parse_cfg_file($akiary_cfg_file,$acfg);

# ���[�U�ݒ�
my $ucfg=
  {
   password=>'',
   diary_cfg_file=>{''=>'cfg/diary.cfg'},
  };
&parse_cfg_file($acfg->{'user_cfg_file'}->{&param('user')},$ucfg);

# ���L�ݒ�
my $dcfg=
  {
   # ���L�e���v���[�g�t�@�C��
   'diary_tmp_file'=>'./tmpbn.html',
   # ���L�f�B���N�g��
   'diary_dir'=>'./',
   # ���b�N�t�@�C���̃f�B���N�g��
   'lock_dir'=>'./',
   # �I�v�V���i�����L�̃e���v���[�g�t�@�C���Əo�̓t�@�C��
   'opt_diary_tmp_file_1'=>'tmpnew.html',
   'opt_diary_file_1'=>'new.html',
   'opt_diary_tmp_file_2'=>'tmpindex.html',
   'opt_diary_file_2'=>'index.html',
   'opt_diary_tmp_file_3'=>'',
   'opt_diary_file_3'=>'',
   'opt_diary_tmp_file_4'=>'',
   'opt_diary_file_4'=>'',
   'opt_diary_tmp_file_5'=>'',
   'opt_diary_file_5'=>'',
   # ���̃X�N���v�g���猩�����L�̃f�B���N�g��
   'diary_url'=>'./index.html',
   # �ŐVn��(latest n times)
   'latest_times'=>'7',
   # �挎�̃o�b�N�i���o�[���Ȃ��ꍇ�̃����N��
   'prev_month'=>'',
   # �����̃o�b�N�i���o�[���Ȃ��ꍇ�̃����N��
   'next_month'=>'',
   # ���L���͎��̑薼�̘g�̒���
   'form_title_size'=>'40',
   # ���L���͎��̓��e�̘g�̑傫��(��)
   'form_body_cols'=>'80',
   # ���L���͎��̓��e�̘g�̑傫��(�s)
   'form_body_rows'=>'10',
   # ���t�\���t�H�[�}�b�g
   'date_format'=>'%Y0�N%M0��%D0��(%W0)',
   # ���t�̐F�̃^�O('font' or 'span')
   'date_color_tag'=>'span',
   # �ڎ��t�H�[�}�b�g: �e�N�̎n��
   'index_format_begin'=>'%Y0�N [ ',
   # �ڎ��t�H�[�}�b�g: �e��
   'index_format_month'=>'%M0��',
   # �ڎ��t�H�[�}�b�g: �e���̊�
   'index_format_between_months'=>' | ',
   # �ڎ��t�H�[�}�b�g: �e�N�̏I���
   'index_format_end'=>' ]<br>',
   # �ڎ��t�H�[�}�b�g: �N�̏���(0:�����A1:�~��)
   'index_format_rev_year'=>'1',
   # �ڎ��t�H�[�}�b�g: ���̏���(0:�����A1:�~��)
   'index_format_rev_month'=>'0',
   # �t�@�C��������
   'dfile_div_mday'=>'',
  };
&parse_cfg_file($ucfg->{'diary_cfg_file'}->{param('diary')},$dcfg);

# v.0.51��S�ʏC�������ɍς܂��邽�߂̕ϊ�
my %CFG;
for (keys %{$dcfg}) {
    $CFG{$_}=$dcfg->{$_};
}

# �X�N���v�g��URL
my $relative_url=$0;
$relative_url=~s/.*[\\\/]//; # �p�X����
my $relative_url_with_query=$relative_url;
$relative_url_with_query.='?'.$ENV{'QUERY_STRING'} if ($ENV{'QUERY_STRING'});
my $OWNFILE=$relative_url_with_query; # v.0.51�Ƃ̌݊����̂���

# �N���W�b�g(<a>����</a>�܂ł͕ύX�s��)
my $SIGNATURE = <<"_SIGNATURE_";
<div style="text-align:center;">
<a href="http://www.hi-ho.ne.jp/yakira/akiary/" target="akiary">Akiary v.$VERSION</a>
</div>
_SIGNATURE_

# �p�X���[�h����
if (param('cmd') eq 'set_password') {
    my $p=&set_password;
    &display_password_setting_page($p);
    exit;
}
unless (&auth_password) {
    &display_password_entry_page;
    exit;
}

#
# �������s
#
if ($FORM{'action'} eq "append"){      # �X�V
    &Append;
} elsif ($FORM{'action'} eq "modify"){ # �C��
    &Modify;
} elsif ($FORM{'action'} eq "delete"){ # �폜
    &Delete;
}

#
# �y�[�W�\��
#
if ($FORM{'page'} eq "now"){ # �V�K
    &PageNow;
} elsif ($FORM{'page'} eq "bn"){ # �o�b�N�i���o�[
    &PageBacknumber;
} elsif ($FORM{'page'} eq "modify"){ # �C��
    &PageModify;
} elsif ($FORM{'page'} eq "deleteYN"){ # �폜�m�F
    &PageDeleteYN;
} else { # �p�X���[�h����
    &display_password_entry_page;
}

exit;

#----------------
# �p�X���[�h�F��
#----------------

sub auth_password {
    my $cpw=$ucfg->{'password'};
    my $ppw=param('password');

    # $cpw eq ''�̂Ƃ��͏��crypt��r���^�ɂȂ��Ă��܂��̂ŁA
    # $cpw ne ''�������ɕt�����Ă���B
    if ($cpw ne '' && crypt($ppw,$cpw) eq $cpw) {
	return 1;
    }
    return 0;
}

#
# �p�X���[�h�ݒ�
#

sub set_password {
    my $user_cfg_file=$acfg->{'user_cfg_file'}->{param('user')};
    # * ��������߂����
    # ���[�U�ݒ�t�@�C�������݂��邩?
    my $du=(-f $user_cfg_file);
    # �V�����p�X���[�h�����͂���Ă��邩?
    my $pn=(defined(param('new_password'))
	    || defined(param('re_enter_new_password')));
    # �p�X���[�h�ݒ�ς�?
    my $up=($ucfg->{'password'} ne '');
    # �p�X���[�h����������?
    my $ap=&auth_password;
    # 2�̐V�����p�X���[�h��������?
    my $mc=(param('new_password') eq param('re_enter_new_password'));

    # * �^���l�\
    # ua:unauth(�p�X���[�h�F�؎��s)
    # um:unmatch(2�̐V�����p�X���[�h�������łȂ�)
    # sc:success(�p�X���[�h�ݒ�����𖞂���)
    # --+-+-+-+-+-+-+-
    # du|0|x|1|1|1|1|1
    # pn|x|0|1|1|1|1|1
    # up|x|x|0|0|1|1|1
    # ap|x|x|x|x|0|1|1
    # mc|x|x|0|1|x|0|1
    # --+-+-+-+-+-+-+-
    # ua|0|0|0|0|1|0|0
    # um|0|0|1|0|0|1|0
    # sc|0|0|0|1|0|0|1
    # --+-+-+-+-+-+-+-
    my $res=
      {
       'unauth'=>0,
       'unmatch'=>0,
       'success'=>0,
      };

    if ($du==1 && $pn==1 && $up==1 && $ap==0) {
	$res->{'unauth'}=1;
    } elsif (($du==1 && $pn==1 && $up==0 && $mc==0) ||
	     ($du==1 && $pn==1 && $up==1 && $ap==1 && $mc==0)) {
	$res->{'unmatch'}=1;
    } elsif (($du==1 && $pn==1 && $up==0 && $mc==1) ||
	     ($du==1 && $pn==1 && $up==1 && $ap==1 && $mc==1)) {
	$res->{'success'}=1;
    }

    # �p�X���[�h���Í������ăt�@�C���ɏ�������
    if ($res->{'success'}==1) {
	my $salt=join '',('.','/',0..9,'A'..'Z','a'..'z')[rand 64,rand 64];
	my $crypted_password=crypt(&param('new_password'),$salt);
	my($sec,$min,$hour,$mday,$mon,$year)=&my_gmtime;
	my $t=sprintf("%d/%02d/%02d %02d:%02d:%02d",
		      $year+1900,$mon+1,$mday,$hour,$min,$sec);
	open(FH,">>$user_cfg_file") or
	  &error('���[�U�ݒ�t�@�C��"'.$user_cfg_file.'"�ɏ������߂܂���B');
	print FH '# by "'.&param('user').'" '.
	  'from '.$ENV{REMOTE_ADDR}.' at '.$t."\n";
	print FH 'password="'.$crypted_password."\"\n";
	close(FH);
    }

    return($res);
}

#
# time()��l�Ԃ��킩��₷�������\���ɕϊ�����B
# ���̍ہAakiary�ݒ�ł�time_zone���l������B
#

sub my_gmtime{
    my($pm,$h,$m) = ($acfg->{'time_zone'} =~ /([+-])(\d\d):?(\d\d)/);
    my $time_offset = $h * 3600 + $m * 60;
    $time_offset *= (-1) if ($pm eq '-');
    gmtime(time + $time_offset);
}

#----------
# �������s
#----------

#
# �X�V
#
sub Append{
    local($date,@dids);
    local(*DATE,*TITLE,*BODY);
    local($file);
    local($tmp,$out);

    # �X�V���s
    $date=sprintf("%04d%02d%02d",$FORM{'year'},$FORM{'mon'},$FORM{'mday'});
    $dids[0]=$date."_".time;
    $DATE{$dids[0]}=$date;
    $TITLE{$dids[0]}=$FORM{'title'};
    $BODY{$dids[0]}=$FORM{'body'};
    $BODY{$dids[0]}=~s/\x0D\x0A/\n/g; # ���s�R�[�h�ϊ�(Win)
    $BODY{$dids[0]}=~s/\x0D/\n/g;     # ���s�R�[�h�ϊ�(Mac)
    $BODY{$dids[0]}=~s/\x0A/\n/g;     # ���s�R�[�h�ϊ�(UNIX)
    $newline = $acfg->{newline};
    $newline =~ s/\\n/\n/g;
    $BODY{$dids[0]} =~ s/\n/$newline/g;

    $file=&date2dfn($date);

    &MakeBNDiary($CFG{'diary_dir'},$file,*DATE,*TITLE,*BODY,*dids);

    # �I�v�V���i�����L�t�@�C�����쐬
    foreach $tmp (grep(/^opt_diary_tmp_file_\d+$/,(keys %CFG))){
	$out=$tmp;
	$out=~s/tmp_//;
	next if ($CFG{$tmp} eq "");
	&MakeOptDiary($CFG{$tmp},$CFG{$out});
    }
}

#
# �C��
#
sub Modify{
    local(@dids,$date);
    local(*DATE,*TITLE,*BODY);
    local($file);
    local($tmp,$out);

    # �X�V���s
    $dids[0]=$FORM{'did'};
    $date=sprintf("%04d%02d%02d",$FORM{'year'},$FORM{'mon'},$FORM{'mday'});
    $DATE{$dids[0]}=$date;
    $TITLE{$dids[0]}=$FORM{'title'};
    $BODY{$dids[0]}=$FORM{'body'};
    $BODY{$dids[0]}=~s/\x0D\x0A/\n/g; # ���s�R�[�h�ϊ�(Win)
    $BODY{$dids[0]}=~s/\x0D/\n/g;     # ���s�R�[�h�ϊ�(Mac)
    $BODY{$dids[0]}=~s/\x0A/\n/g;     # ���s�R�[�h�ϊ�(UNIX)
    $newline = $acfg->{newline};
    $newline =~ s/\\n/\n/g;
    $BODY{$dids[0]} =~ s/\n/$newline/g;

    $file=&date2dfn($date);

    &MakeBNDiary($CFG{'diary_dir'},$file,*DATE,*TITLE,*BODY,*dids);

    # �o�b�N�i���o�[�Ԉړ������ꍇ�͑O�̃t�@�C���������
    # (��)2000�N1��1���̂�1999�N12��31���ɏC�������ꍇ�A200001.html�������
    if ($file ne $FORM{'dfn'}){
	&MakeBNDiary($CFG{'diary_dir'},$FORM{'dfn'},'','','',*dids);
    }

    # �I�v�V���i�����L�t�@�C�����쐬
    foreach $tmp (grep(/^opt_diary_tmp_file_\d+$/,(keys %CFG))){
	$out=$tmp;
	$out=~s/tmp_//;
	next if ($CFG{$tmp} eq "");
	&MakeOptDiary($CFG{$tmp},$CFG{$out});
    }

    # �C�����ʂŁu���̂܂܁v��I�������Ƃ��ɂ̓t�@�C������ύX
    if ($FORM{'page'} eq 'modify'){
	$FORM{'dfn'}=$file;
    }
}

#
# �폜
#
sub Delete{
    local(@dids);
    local($tmp,$out);

    $dids[0]=$FORM{'did'};

    # �폜
    &MakeBNDiary($CFG{'diary_dir'},$FORM{'dfn'},'','','',*dids);

    # �I�v�V���i�����L�t�@�C�����쐬
    foreach $tmp (grep(/^opt_diary_tmp_file_\d+$/,(keys %CFG))){
	$out=$tmp;
	$out=~s/tmp_//;
	next if ($CFG{$tmp} eq "");
	&MakeOptDiary($CFG{$tmp},$CFG{$out});
    }
}


#------------
# �y�[�W�\��
#------------

#
# �p�X���[�h���̓y�[�W�\��
#

sub display_password_entry_page{
    my $p=
      {
       'url'=>$relative_url_with_query,
       'password_entry'=>0,
      };
    if (defined(param('password'))){
	$p->{'password_entry'}=1;
    }

    my $html=&HtmlHeader('�p�X���[�h����');
    $html.=<<'_END_OF_HTML_';
<hr>
<TMPL_IF NAME="password_entry">
<p>�p�X���[�h���Ⴂ�܂��B</p>
</TMPL_IF>
<form method="POST" action="<TMPL_VAR NAME="url">">
<input type="hidden" name="page" value="now">
�p�X���[�h
<input type="password" name="password">
<input type="submit" value="����">
<input type="reset" value="���">
</form>
_END_OF_HTML_
    $html.=&HtmlFooter;
    &PrintHTTP(&template_output($html,$p));
}

#
# �p�X���[�h�ݒ�y�[�W�\��
#

sub display_password_setting_page {
    my $p=shift;
    $p->{'url'}=$relative_url_with_query;
    $p->{'url_nocmd'}=$relative_url_with_query;
    $p->{'url_nocmd'}=~s/cmd=set_password//;
    if ($ucfg->{'password'} ne '') {
	$p->{'password_defined'}=1;
    }

    my $html=&HtmlHeader('�p�X���[�h�ݒ�');
    $html.=<<'_END_OF_HTML_';
<hr>
<TMPL_IF NAME="unauth">
 <h2>���b�Z�[�W</h2>
 <p>�p�X���[�h���قȂ�܂��B������x���͂��ĉ������B</p>
</TMPL_IF>

<TMPL_IF NAME="unmatch">
 <h2>���b�Z�[�W</h2>
 <p>
  �V�����p�X���[�h�Ɗm�F�p�̐V�����p�X���[�h���قȂ�܂��B
  ������x���͂��ĉ������B
 </p>
</TMPL_IF>

<TMPL_IF NAME="success">
 <h2>���b�Z�[�W</h2>
 <p>�p�X���[�h��ݒ肵�܂����B</p>
 <p>�����ē��L�������Ƃ��́A
  <a href="<TMPL_VAR NAME="url_nocmd">"><TMPL_VAR NAME="url_nocmd"></a>
  ���N���b�N���ĉ������B
 </p>
</TMPL_IF>

<h2>�V�p�X���[�h����</h2>
<form method="post" action="<TMPL_VAR NAME="url">">
 <table>

  <TMPL_IF NAME="password_defined">
   <tr>
    <td>Old password:</td>
    <td><input type="password" name="password"></td>
   </tr>
  </TMPL_IF>

  <tr>
   <td>New password:</td>
   <td><input type="password" name="new_password"></td>
  </tr>
  <tr>
   <td>Re-enter new password:</td>
   <td><input type="password" name="re_enter_new_password"></td>
  </tr>
  <tr>
   <td></td>
   <td>
    <input type="submit" value="����">
    <input type="reset" value="���">
   </td>
 </table>
</form>
_END_OF_HTML_
    $html.=&HtmlFooter;
    &PrintHTTP(&template_output($html,$p));
}

#
# �ȈՔ�HTML::Template->output
#

sub template_output{
    my $t=shift; # html template
    my $p=shift; # parameters

    # <TMPL_IF NAME="name">...</TMPL_IF>
    $t=~s/<TMPL_IF NAME="(\w+)">(.*?)<\/TMPL_IF>/($p->{$1})?$2:''/egs;

    # <TMPL_VAR NAME="name">
    $t=~s/<TMPL_VAR NAME="(\w+)">/$p->{$1}/g;
    return($t);
}

#
# �V�K��ʕ\��
#
sub PageNow{
    local(@files,$file,$contents);
    local(*date,*title,*body);
    local(%dfn);
    local($html);
    local(%tmp,$days);
    local($syear,$smon,$smday)=&get_todays_date;
    local($sdate);
    local($escpw)=&escapeHTML($FORM{'password'});

    # ���L�t�@�C�����擾
    opendir(DIR,$CFG{'diary_dir'})
	|| &error("���L�f�B���N�g�� $CFG{'diary_dir'} ���J���܂���B");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    # ���L�t�@�C����ǂ�
    foreach $file (reverse(@files)){
	open(FILE,"$CFG{'diary_dir'}/$file")
	    || &error("���L�t�@�C�� $CFG{'diary_dir'}/$file ���J���܂���B");
	$contents=join("",<FILE>);
	close(FILE);
	# ���L����؂�o���ADID�ADATE�ATITLE�ABODY���o
	&Contents2DTB($contents,*date,*title,*body);
	# �eDID�̓��L�t�@�C����
	foreach(keys %date){
	    $dfn{$_}=$file unless defined($dfn{$_});
	}
	# �K�萔�W�߂���I���
	last if (scalar(keys %date)>=$CFG{'latest_times'});
    }

    #
    # �\������
    #
    $html=&HtmlHeader("�V�K");
    $html.=<<"_HTML_";
<hr>
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="append">
_HTML_
    # ���L���̓e�[�u���\��
    %tmp=("year",$syear, "mon",$smon, "mday",$smday,
	  "rows",$CFG{'form_body_rows'}, "cols",$CFG{'form_body_cols'},
	  "size",$CFG{'form_title_size'}, "submit","�V�K");
    $html.=&DiaryInputTable(*tmp);
    $html.=<<"_HTML_";
<input type="hidden" name="page" value="now">
</form>
_HTML_

    # �C��/�폜
    if (%date){
	$html.="<hr>\n";
	$days=0;
	foreach(reverse &SortedDID(*date)){
	    last if (++$days>$CFG{'latest_times'});
	    $date=$date{$_};
	    $title=&escapeHTML($title{$_});
	    $sdate=&date2sdate($date);
	    $html.=<<"_HTML_";
<form method="post" action="$OWNFILE">
$sdate $title 
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="noop">
<input type="radio" name="page" value="modify" checked>�C��
<input type="radio" name="page" value="deleteYN">�폜
<input type="hidden" name="dfn" value="$dfn{$_}">
<input type="hidden" name="did" value="$_">
<input type="hidden" name="retpage" value="now">
<input type="submit" value="����">
</form>
_HTML_
	}
    }

    # �t�@�C���I��
    if (@files){
	$html.="<hr>\n";
	$html.=&HtmlFileSelect($files[-1],@files);
    }

    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# �o�b�N�i���o�[��ʕ\��
#
sub PageBacknumber{
    local($contents);
    local(*date,*title,*body);
    local($escpw)=&escapeHTML($FORM{'password'});

    # �y�[�W�\��
    local($html)=&HtmlHeader("�o�b�N�i���o�[$FORM{'dfn'}");
    $html.="<hr>\n";

    # �t�@�C���ǂݍ���
    open(FH,"$CFG{'diary_dir'}/$FORM{'dfn'}")
	|| ($html.="<p>$FORM{'dfn'}�͂���܂���B</p>\n");
    $contents=join("",<FH>);
    close(FH);

    # ���L�t�@�C�����
    &Contents2DTB($contents,*date,*title,*body);

    # �o�b�N�i���o�[�ꗗ
    foreach(&SortedDID(*date)){
	$date=$date{$_};
	$title=&escapeHTML($title{$_});
	$sdate=&date2sdate($date{$_});
	$html.=<<"_HTML_";
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="noop">
<input type="hidden" name="dfn" value="$FORM{'dfn'}">
<input type="hidden" name="did" value="$_">
$sdate $title 
<input type="radio" name="page" value="modify" checked>�C��
<input type="radio" name="page" value="deleteYN">�폜
<input type="hidden" name="retpage" value="bn">
<input type="submit" value="����">
</form>
_HTML_
    }

    # �V�K��ʂ�
    $html.=<<"_HTML_";
<hr>
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="noop">
<input type="hidden" name="page" value="now">
<input type="submit" value="�V�K��ʂ�">
</form>
_HTML_

    # ���L�t�@�C�����擾
    opendir(DIR,$CFG{'diary_dir'})
	|| &error("���L�f�B���N�g�� $CFG{'diary_dir'} ���J���܂���B");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);
    $html.=&HtmlFileSelect($FORM{'dfn'},@files);

    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# �C���\��
#
sub PageModify{
    local($contents);
    local(*date,*title,*body);
    local($syear,$smon,$smday);
    local($html);
    local($escpw)=&escapeHTML($FORM{'password'});
    local(%tmp);

    # �t�@�C���ǂݍ���
    open(FILE,"$CFG{'diary_dir'}/$FORM{'dfn'}")
	|| &error("���L�t�@�C���u$CFG{'diary_dir'}/$FORM{'dfn'}�v���J���܂���B");
    $contents=join("",<FILE>);
    close(FILE);

    # ���L�t�@�C�����
    &Contents2DTB($contents,*date,*title,*body);

    # �X�V/�폜
    ($date,$title,$body)
	=($date{$FORM{'did'}},$title{$FORM{'did'}},$body{$FORM{'did'}});
    ($syear,$smon,$smday)=($date=~/^(\d{4})(\d{2})(\d{2})/);
	if ($acfg->{newline} eq '<br>') {
	    $body=~tr/\x0D\x0A//d; # ���s�R�[�h�폜
	    $body=~s/<br>/\n/ig;
	}

    # �y�[�W�\��
    $html=&HtmlHeader("�C��");
    $html.=<<"_HTML_";
<hr>
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="modify">
<input type="hidden" name="dfn" value="$FORM{'dfn'}">
<input type="hidden" name="did" value="$FORM{'did'}">
_HTML_

    %tmp=("year",$syear, "mon",$smon, "mday",$smday,
	  "size",$CFG{'form_title_size'},
	  "rows",$CFG{'form_body_rows'}, "cols",$CFG{'form_body_cols'},
	  "title",$title, "body",$body, "submit","�C��");
    $html.=&DiaryInputTable(*tmp);

    $html.=<<"_HTML_";
<p>
�C������
<input type="radio" name="page" value="modify" checked>���̂܂�
<input type="radio" name="page" value="$FORM{'retpage'}">���ǂ�
<input type="hidden" name="retpage" value="$FORM{'retpage'}">
</p>
</form>
<hr>
<center>
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="noop">
<input type="hidden" name="page" value="$FORM{'retpage'}">
<input type="hidden" name="dfn" value="$FORM{'dfn'}">
<input type="submit" value="���ǂ�">
</form>
</center>
_HTML_

    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# �폜�m�F��ʕ\��
#
sub PageDeleteYN{
    local($contents);
    local(*date,*title,*body);
    local($sdate);
    local($html);
    local($escpw)=&escapeHTML($FORM{'password'});

    # �t�@�C���ǂݍ���
    open(FILE,"$CFG{'diary_dir'}/$FORM{'dfn'}")
	|| &error("���L�t�@�C���u$CFG{'diary_dir'}/$FORM{'dfn'}�v���J���܂���B");
    $contents=join("",<FILE>);
    close(FILE);

    # ���L�t�@�C�����
    &Contents2DTB($contents,*date,*title,*body);

    $sdate=&date2sdate($date{$FORM{'did'}});
    $title=&escapeHTML($title{$FORM{'did'}});
    $body=$body{$FORM{'did'}};
    $body=&escapeHTML($body);
    $body=~s/&lt;br&gt;/<br>/ig;

    # �\��
    $html=&HtmlHeader("�폜�m�F");
    $html.=<<"_HTML_";
<hr>
<p>�폜���Ă���낵���ł����H</p>
<table border="1">
 <tr>
  <th>���t</th>
  <td>$sdate</td>
 </tr>
 <tr>
  <th>�薼</th>
  <td>$title</td>
 </tr>
 <tr>
  <th>���e</th>
  <td>$body</td>
 </tr>
</table>
<form method="post" action="$OWNFILE">
 <input type="hidden" name="password" value="$escpw">
 <input type="radio" name="action" value="delete">�͂�
 <input type="radio" name="action" value="noop" checked>������
 <input type="hidden" name="dfn" value="$FORM{'dfn'}">
 <input type="hidden" name="did" value="$FORM{'did'}">
 <input type="hidden" name="page" value="$FORM{'retpage'}">
 <input type="submit" value="����">
 <input type="reset" value="���">
</form>
_HTML_
    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#----------------
# �T�u���[�`���Q
#----------------

#
# �ݒ�t�@�C�����
# �y�����z
#  $cfg_file: �ݒ�t�@�C����
#  $cfg: �ݒ�p�n�b�V���ϐ��ւ̃��t�@�����X
# �y���Ӂz
#  �ݒ�t�@�C������NULL('')�̂Ƃ��͑����Ƀ��^�[���B
#  ���Ȃ킿�v���O�������̃f�t�H���g�l���p������B
#  �ݒ�p�n�b�V���ϐ�$cfg�͎��O�Ƀf�t�H���g�l��^����K�v����B
#  defined�łȂ��ꍇ�̓G���[�ƂȂ�B
#  $ENV{'xxx'}�͓W�J�\(for Hi-HO)
#

sub parse_cfg_file ($$){
    my($cfg_file) = shift;
    my($cfg) = shift;

    return if ($cfg_file eq '');

    open(FH,$cfg_file) || &error('�ݒ�t�@�C��"'.$cfg_file.'"���J���܂���B');
    while(<FH>){
	next if (/^\s*$/);
	next if (/^#/);
	unless (/^(-)?(\w+)((?:\{"\w*"\}){0,2})\s*=\s*("[^"]*")/){
	    &error('�ݒ�t�@�C��'.$cfg_file.'��'.$..'�s�ڂ����@�G���[�ł��B');
	}
	my($k,$ke,$v)=($2,$3,$4);
	unless (defined($cfg->{$k})){
	    &error('�ݒ�t�@�C��'.$cfg_file.'�̐ݒ薼'.$k.'�͐ݒ�ł��܂���B'.
		   'akiary.cgi�Ńf�t�H���g�l��ݒ肵�ĉ������B');
	}
	$v =~ s/"//g;
	$v =~ s/\$ENV\{'(\w+)'\}/$ENV{$1}/g;

	if ($ke =~ /\{"(\w*)"\}\{"(\w*)"\}/) {
	    ${ $cfg->{$k} }{$1}{$2}=$v;
	} elsif ($ke =~ /\{"(\w*)"\}/) {
	    ${ $cfg->{$k} }{$1}=$v;
	} else {
	    $cfg->{$k}=$v;
	}
    }
    close(FH);
}

#
# CGI�̃p�����[�^(�t�H�[������)�̃f�R�[�h
#   �Q�l����: Scott Guelich et al., "CGI�v���O���~���O��2��", 4��3��, p.94.
#

sub parse_param{
    my %form_data;
    my $name_value;
    my @name_value_pairs = split /&/, $ENV{QUERY_STRING};

    if ( $ENV{REQUEST_METHOD} eq 'POST') {
	my $query = "";
	read(STDIN, $query, $ENV{CONTENT_LENGTH}) == $ENV{CONTENT_LENGTH}
	  or return undef;
	push @name_value_pairs, split /&/, $query;
    }

    foreach $name_value (@name_value_pairs) {
	my($name,$value) = split /=/, $name_value;

	$name =~ tr/+/ /;
	$name =~ s/%([a-f0-9][a-f0-9])/chr(hex($1))/egi;

	$value = "" unless defined $value;
	$value =~ tr/+/ /;
	$value =~ s/%([a-f0-9][a-f0-9])/chr(hex($1))/egi;

	$form_data{$name} = $value;
    }

    # akiary�^�O�̏���
    if ( $form_data{'title'} ){
	$form_data{'title'}=~s/<(!--\s*\/?akiary[^>]*)>/&lt;$1&gt;/ig
    }
    if ( $form_data{'body'} ) {
	$form_data{'body'}=~s/<(!--\s*\/?akiary[^>]*)>/&lt;$1&gt;/ig;
    }

    return %form_data;
}

#
# ����CGI.pm�𓱓����邽�߂̕z��
#

sub param{
    my $key = shift;
    if (defined($FORM{$key})) {
	return $FORM{$key};
    } else {
	return undef;
    }
}

#
# Print HTTP
#
sub PrintHTTP{
    print "Content-Type:text/html;charset=", $acfg->{charset}, "\n\n", $_[0];
}

#
# HTML�̃w�b�_�[��
#
sub HtmlHeader{
    return <<"_HTML_";
<html>
<head>
<title>Akiary($_[0])</title>
<style>
<!--
div.title {
 background-color: #000000;
 border: 3px solid #b0b0b0;
 color: #e0e0e0;
 font-weight: bold;
 font-size: 150%;
 padding: 5 5 5 5; /* top right bottom left */
 text-align: center;
 width: 100%;
}
div.subtitle {
 font-weight: bold;
 text-align: center;
}
span.weekday {color:black;}
span.saturday {color:blue;}
span.sunday {color:red;}
-->
</style>
</head>
<body>
[<a href="$CFG{'diary_url'}" target="diary">���L</a>]
<div class="title">Akiary</div>
<div class="subtitle">$_[0]</div>
_HTML_
}

#
# HTML�̃t�b�^�[��
#
sub HtmlFooter{
    return <<"_HTML_";
<hr>
$SIGNATURE</body>
</html>
_HTML_
}

#
# �t�@�C���I����HTML
# �E����
#   $sfile: �f�t�H���g�I���̃t�@�C����
#   @files: �t�@�C����
# �E�Ԓl
#   �t�@�C���I����HTML
#
sub HtmlFileSelect{
    local($sfile,@files)=@_;
    local($html);
    local($escpw)=&escapeHTML($FORM{'password'});

    # �t�@�C�����Ȃ���ΏI���
    return unless (@files);

    # �t�@�C���I��HTML�쐬
    $html.=<<"_HTML_";
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="noop">
<input type="hidden" name="page" value="bn">
<select name="dfn">
_HTML_
    foreach(@files){
	if ($_ eq $sfile){
	    $html.="<option value=\"$_\" selected>$_\n";
	} else {
	    $html.="<option value=\"$_\">$_\n";
	}
    }
    $html.=<<"_HTML_";
</select>
<input type="submit" value="�I��">
</form>
_HTML_
}

#
# ���t�𐔎����當����ɕϊ�
# (��) 20001020 �� <font color="#000000">2000�N10��20��(��)</font>
# �y�����z
#  $date  : �����̓��t 
#  $format: �t�H�[�}�b�g
#    %Y0 1900-9999
#    %Y1 00-99
#    %Y2 1-8011(��������)
#    %M0 1-12
#    %M1 01-12
#    %M2 Jan-Dec
#    %M3 January-December
#    %D0 1-31
#    %D1 01-31
#    %W0 ��-�y
#    %W1 Sun-Sat
#    %W2 Sunday-Saturday
#    �f�t�H���g��"%Y0�N%M0��%D0��(%W0)"
#
sub date2sdate{
    local($date,$format,$no_tag)=@_;
    local($y0,$m0,$d0,$w);
    local(@m2,@m3,@w0,@w1,@w2);
    local($color,$class,$sdate);

    $format=$CFG{'date_format'} if ($format eq "");

    # �N����
    ($y0,$m0,$d0)=($date=~/(\d{4})(\d{2})(\d{2})/);
    $y0=1900 if ($y0 < 1900);
    $m0=1 if ($m0 < 1);
    $m0=12 if ($m0 > 12);
    $d0=1 if ($d0 < 1);
    $d0=31 if ($d0 > 31);

    # �j��(0:���j; 6:�y�j)
    $w=&GetWdayZeller($y0,$m0,$d0);

    # ������ϊ��̏���
    @m2=('Jan','Feb','Mar','Apr','May','Jun',
	 'Jul','Aug','Sep','Oct','Nov','Dec');
    @m3=('January','February','March','April','May','June',
	 'July','August','September','October','November','December');
    @w0=('��','��','��','��','��','��','�y');
    @w1=('Sun','Mon','Tue','Wed','Thu','Fri','Sat');
    @w2=('Sunday','Monday','Tuesday','Wednesday',
	 'Thursday','Friday','Saturday');

    # ��������t
    $sdate=$format;
    $sdate=~s/%Y0/$y0/g;                      # 4������
    $sdate=~s/%Y1/sprintf("%02d",$y0%100)/eg; # 2������
    $sdate=~s/%Y2/$y0-1988/eg;                # ��������
    $sdate=~s/%M0/sprintf("%d",$m0)/eg;   # ��
    $sdate=~s/%M1/sprintf("%02d",$m0)/eg; # ��(0�t��)
    $sdate=~s/%M2/$m2[$m0-1]/g;          # ��(�p��Z�k)
    $sdate=~s/%M3/$m3[$m0-1]/g;          # ��(�p��)
    $sdate=~s/%D0/sprintf("%d",$d0)/eg;   # ��
    $sdate=~s/%D1/sprintf("%02d",$d0)/eg; # ��(0�t��)
    $sdate=~s/%W0/$w0[$w]/g; # �j��
    $sdate=~s/%W1/$w1[$w]/g; # �j��(�p��Z�k)
    $sdate=~s/%W2/$w2[$w]/g; # �j��(�p��)

    if ($no_tag) {

    } elsif ($CFG{'date_color_tag'} eq 'font') {
	$color="#000000";              # �����̐F
	$color="#DD0000" if ($w == 0); # ���j���̐F
	$color="#3333FF" if ($w == 6); # �y�j���̐F
	$sdate="<font color=\"$color\">$sdate</font>";
    } elsif ($CFG{'date_color_tag'} eq 'span') {
	$class="weekday";               # �����̐F
	$class="sunday"   if ($w == 0); # ���j���̐F
	$class="saturday" if ($w == 6); # �y�j���̐F
	$sdate="<span class=\"$class\">$sdate</span>";
    }
    # ���^�[��
    return $sdate;
}

#
# �G���[
#
sub error{
    local($html)=&HtmlHeader("�G���[");
    $html.="<hr>\n<p>@_</p>\n";
    $html.=&HtmlFooter;
    &PrintHTTP($html);
    exit;
}

#
# �f�o�O�p
#
sub debug{
    local($html)=&HtmlHeader("�f�o�O");
    $html.="<hr>\n";
    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# �����̔N�����𓾂�
#

sub get_todays_date{
    my($pm,$h,$m)=($acfg->{'time_zone'}=~/([+-])(\d\d):?(\d\d)/);
    my $time_offset = $h*3600+$m*60;
    $time_offset *= (-1) if ($pm eq "-");
    my($mday,$mon,$year)=(gmtime(time+$time_offset))[3..5];
    return($year+1900,$mon+1,$mday);
}

#
# ���L�t�@�C���̒��g����A���t�ƃ^�C�g���Ɩ{���𒊏o����
#

sub Contents2DTB{
    local($contents,*date,*title,*body)=@_;
    local($did,$tb,$d,$t,$b);

    # Perl4�ł́u?�v�ōŒZ��v�������Ȃ����߈ȉ��̂悤�ɏ���
    while($contents=~/<!--\s*akiary_diary did=(\S+) date=(\d+)\s*-->/){
	($did,$d)=($1,$2);
	$contents=$'; # �}�b�`�������������̕���
	$contents=~/<!--\s*\/akiary_diary\s*-->/;
	$contents=$';
	$tb=$`; # <!--akiary_diary-->����<!--/akiary_diary-->�܂�
	($t)=($tb=~/<!--\s*akiary_title\s*-->([\000-\377]*)<!--\s*\/akiary_title\s*-->/);
	($b)=($tb=~/<!--\s*akiary_body\s*-->([\000-\377]*)<!--\s*\/akiary_body\s*-->/);
	$date{$did}=$d;
	$title{$did}=$t;
	$body{$did}=$b;
    }
}

#
# zeller�̌����ɂ��j���Z�o�֐�
# http://wdic.asuka.net/?title=Zeller%A4%CE%B8%F8%BC%B0
#

sub GetWdayZeller{
    local($year,$mon,$mday)=@_;

    if (($mon==1) || ($mon==2)){
	$year--;
	$mon+=12;
    }
    ($year + int($year/4) - int($year/100) + int($year/400)
     + int((13 * $mon + 8)/5) + $mday) % 7;
}

#
# ���L�e���v���[�g�t�@�C������͂���
#

sub AnalyzeTmpbn{
    local(*contents,*head,*opt,*body,*foot)=@_;

    if ($contents=~/<!--\s*akiary_diary([^>]*)\s*-->([\000-\377]*)<!--\s*\/akiary_diary\s*-->/i){
	$head=$`; # �w�b�_��
	$opt=$1;  # akiary_diary�̃I�v�V����
	$body=$2; # akiary_diary�̖{��
	$foot=$'; # �t�b�^��

	# (1)�{������akiary_diary�^�O���Ȃ�
	# (2)�{������akiary_title�^�O�͂ЂƂ̂�
	# (3)�{������akiary_body�^�O�͂ЂƂ̂�
	if ($body !~ /<!--\s*akiary_diary[^>]*\s*-->/i &&
	    $body !~ /<!--\s*\/akiary_diary\s*-->/i &&
	    ($body =~ s/<!--\s*akiary_title\s*-->/$&/ig) == 1 &&
	    ($body =~ s/<!--\s*akiary_body\s*-->/$&/ig) == 1) {
	    return(1); # ��͐��������1��Ԃ�
	}
    }
}

#
# ���L�e���v���[�g�t�@�C���̃G���[
#
sub ErrorTmpbn{
    local($html)=&HtmlHeader("���L�e���v���[�g�t�@�C���̃G���[");
    $html.=<<END_OF_TEXT;
<hr>
<p>
�G���[�̌����͈ȉ���6�_�̂����ꂩ�ł��B<br>
<ol>
<li>�u<tt>&lt;!--akiary_diary--&gt;</tt>�v���u<tt>&lt;!--/akiary_diary--&gt;</tt>�v������܂���B
<li>�u<tt>&lt;!--akiary_diary--&gt;</tt>�v���u<tt>&lt;!--/akiary_diary--&gt;</tt>�v��2�ȏ゠��܂��B
<li>�u<tt>&lt;!--akiary_diary--&gt;</tt>�v�Ɓu<tt>&lt;!--/akiary_diary--&gt;</tt>�v�̊ԂɁu<tt>&lt;!--akiary_title--&gt;</tt>�v������܂���B
<li>�u<tt>&lt;!--akiary_diary--&gt;</tt>�v�Ɓu<tt>&lt;!--/akiary_diary--&gt;</tt>�v�̊ԂɁu<tt>&lt;!--akiary_title--&gt;</tt>�v��2�ȏ゠��܂��B
<li>�u<tt>&lt;!--akiary_diary--&gt;</tt>�v�Ɓu<tt>&lt;!--/akiary_diary--&gt;</tt>�v�̊ԂɁu<tt>&lt;!--akiary_body--&gt;</tt>�v������܂���B
<li>�u<tt>&lt;!--akiary_diary--&gt;</tt>�v�Ɓu<tt>&lt;!--/akiary_diary--&gt;</tt>�v�̊ԂɁu<tt>&lt;!--akiary_body--&gt;</tt>�v��2�ȏ゠��܂��B
</ol>
</p>
END_OF_TEXT
    $html.=&HtmlFooter;
    &PrintHTTP($html);
    exit;
}

#
# ���L���̓e�[�u���\��
#
# �y�����z
#   $opt{"year"}  : �f�t�H���g�I���̔N
#   $opt{"mon"}   : �f�t�H���g�I���̌�
#   $opt{"mday"}  : �f�t�H���g�I���̓�
#   $opt{"size"}  : �薼�̒���
#   $opt{"cols"}  : ���e�̗�
#   $opt{"rows"}  : ���e�̍s��
#   $opt{"title"} : �薼
#   $opt{"body"}  : ���e
#   $opt{"submit"}: submit�{�^��
# �y�Ԓl�z
#   ���L���̓e�[�u��(<TABLE>����</TABLE>�܂�)
#

sub DiaryInputTable{
    local(*opt)=@_;
    local($option0112,$option0131);
    local($title)=&escapeHTML($opt{"title"});
    local($body)=&escapeHTML($opt{"body"});

    # ���I��
    foreach(1..12){
	if ($_ == $opt{"mon"}){
	    $option0112.="<option value=\"$_\" selected>$_";
	} else {
	    $option0112.="<option value=\"$_\">$_";
	}
    }
    # ���I��
    foreach(1..31){
	if ($_ == $opt{"mday"}){
	    $option0131.="<option value=\"$_\" selected>$_";
	} else {
	    $option0131.="<option value=\"$_\">$_";
	}
    }

    return <<END_OF_TEXT;
<table>
 <tr>
  <th>���t</th>
  <td>
   <input type="text" name="year" value="$opt{'year'}" size="4">�N
   <select name="mon">$option0112</select>��
   <select name="mday">$option0131</select>��
  </td>
 </tr>
 <tr>
  <th>�薼</th>
  <td>
   <input type="text" name="title" value="$title" size="$opt{'size'}">
  </td>
 </tr>
 <tr>
  <th>���e</th>
  <td>
   <textarea rows="$opt{'rows'}" cols="$opt{'cols'}" wrap="soft" name="body">$body</textarea>
  </td>
 </tr>
 <tr>
  <th></th>
  <td>
   <input type="submit" value="$opt{'submit'}">
   <input type="reset" value="���">
  </td>
 </tr>
</table>
END_OF_TEXT
}

#
# rename�����t�@�C�����b�N
# (�Q�l���� http://www.din.or.jp/~ohzaki/perl.htm)
#

sub my_flock {
    local(*lfh)=@_;
    local(@filelist);
    local($i);

    %lfh=('dir',$CFG{'lock_dir'},
	  'basename','lockfile',
	  'timeout',60,
	  'trytime',10);

    $lfh{'path'} = "$lfh{'dir'}/$lfh{'basename'}";
    for ($i = 0; $i < $lfh{'trytime'}; $i++) {
	return 1 if (rename($lfh{'path'},$lfh{'current'}=$lfh{'path'}.time));
	sleep 1;
    }
    opendir(LOCKDIR, $lfh{'dir'})
	|| &error("���b�N�f�B���N�g�� $lfh{'dir'} ���J���܂���B");
    @filelist = readdir(LOCKDIR);
    closedir(LOCKDIR);
    foreach (@filelist) {
	if (/^$lfh{'basename'}(\d+)/) {
	    return 1 if (time - $1 > $lfh{'timeout'} &&
		rename("$lfh{'dir'}/$_",$lfh{'current'}=$lfh{'path'}.time));
	    last;
	}
    }
    0; # ���b�N���s
}

#
# �A�����b�N
#

sub my_funlock {
    local(*lfh)=@_;
    rename($lfh{'current'},$lfh{'path'});
}

#
# MakeBNDiary -- �o�b�N�i���o�[�t�@�C���쐬�֐� --
#
# �y�����z
#   $dir  : �o�b�N�i���o�[�f�B���N�g����
#   $file : �o�b�N�i���o�[�t�@�C����
#   *date : ���t <$date{$did}>
#   *title: �薼 <$title{$did}>
#   *body : ���e <$body{$did}>
#   *dids : �ǉ�/�폜������L��DiaryID <@dids>
# �y���O�ɏ������Ă����O���[�o���ϐ��z
#   $TMPBNFILE: �o�b�N�i���o�[�p�e���v���[�g�t�@�C��
#   $SIGNATURE: ����
#   $CFG{'prev_month'}: �挎�ւ̃����N��(�f�t�H���g)
#   $CFG{'next_month'}: �����ւ̃����N��(�f�t�H���g)
# �y�ǉ�����Ƃ��z
#   $date{$did}�A$title{$did}�A$body{$did}��p�ӂ��Ă���
#   &MakeDiary($dir,$file,*date,*title,*body,*dids)�����s
# �y�폜����Ƃ��z
#   &MakeDiary($dir,$file,'','','',*dids)�����s
# �y����z
#   (1)�o�b�N�i���o�[�p�e���v���[�g�t�@�C����ǂ�
#   (2)�t�@�C�����b�N
#   (3)�o�b�N�i���o�[�t�@�C����ǂ�
#   (4)�ϐ���œ��L��ǉ�/�폜����
#   (5)�o�b�N�i���o�[�t�@�C�����쐬����
#   (6)�t�@�C�����b�N����
#   (7)�K�v�Ȃ�ΐ挎����ї����̃t�@�C������X�V����
#

sub MakeBNDiary{
    local($dir,$file,*date,*title,*body,*dids)=@_;

    local($filecont);
    local($tmpbnhead,$opt,$tmpbnbody,$tmpbnfoot);
    local($tmpbnrev);
    local(%lfh);
    local(%bndate,%bntitle,%bnbody);
    local($akiary_prevmonth,$akiary_nextmonth);
    local($prevmonth,$nextmonth);
    local($existbefore,$existafter);
    local(@k);
    local($tmp);

    #
    # (1)�o�b�N�i���o�[�p�e���v���[�g�t�@�C����ǂ�
    #

    # �ǂݍ���
    open(FH,$CFG{'diary_tmp_file'})
	|| &error("���L�e���v���[�g�t�@�C�� $CFG{'diary_tmp_file'} ���J���܂���B");
    $filecont=join("",<FH>);
    close(FH);

    # ���&�G���[�`�F�b�N
    &AnalyzeTmpbn(*filecont,*tmpbnhead,*opt,*tmpbnbody,*tmpbnfoot)
	|| &ErrorTmpbn;
    $tmpbnrev=1 if ($opt=~/reverse/);

    #
    # (2)�t�@�C�����b�N
    #

    &my_flock(*lfh) || &error("�t�@�C�����b�N�Ɏ��s���܂����B");

    #
    # (3)�o�b�N�i���o�[�t�@�C����ǂ�
    #

    if (open(FH,"$dir/$file")){ # open�ł��Ȃ��Ă��G���[���b�Z�[�W�͕s�v
	$filecont=join("",<FH>);
	# ���L����؂�o���ADID�ADATE�ATITLE�ABODY���o
	&Contents2DTB($filecont,*bndate,*bntitle,*bnbody);
	close(FH);
    }

    #
    # (4)�ϐ���Ńo�b�N�i���o�[���쐬
    #

    # �挎/�����ւ̃����N
    if ($tmpbnhead=~/<!--\s*akiary_prevmonth\s*-->/i ||
	$tmpbnfoot=~/<!--\s*akiary_prevmonth\s*-->/i ){
	$akiary_prevmonth=1; # �挎�ւ̃����N����
    }
    if ($tmpbnhead=~/<!--\s*akiary_nextmonth\s*-->/i ||
	$tmpbnfoot=~/<!--\s*akiary_nextmonth\s*-->/i ){
	$akiary_nextmonth=1; # �����ւ̃����N����
    }
    # �挎/�����ւ̃����N����
    if ($akiary_prevmonth==1 || $akiary_nextmonth==1){
	# �O��Ǝ���̃t�@�C����T��
	($prevmonth,$nextmonth)=&GetPNFile($dir,$file);
	# �挎�ւ̃����N�쐬
	if ($prevmonth ne ""){
	    $tmpbnhead=~s/<!--\s*akiary_prevmonth\s*-->/<a href="$prevmonth">/ig;
	    $tmpbnhead=~s/<!--\s*\/akiary_prevmonth\s*-->/<\/a>/ig;
	    $tmpbnfoot=~s/<!--\s*akiary_prevmonth\s*-->/<a href="$prevmonth">/ig;
	    $tmpbnfoot=~s/<!--\s*\/akiary_prevmonth\s*-->/<\/a>/ig;
	}
	# �����ւ̃����N�쐬
	if ($nextmonth ne ""){
	    $tmpbnhead=~s/<!--\s*akiary_nextmonth\s*-->/<a href="$nextmonth">/ig;
	    $tmpbnhead=~s/<!--\s*\/akiary_nextmonth\s*-->/<\/a>/ig;
	    $tmpbnfoot=~s/<!--\s*akiary_nextmonth\s*-->/<a href="$nextmonth">/ig;
	    $tmpbnfoot=~s/<!--\s*\/akiary_nextmonth\s*-->/<\/a>/ig;
	}
    }

    # �����}��
    $tmpbnfoot=~s/<\/body>/$SIGNATURE<\/body>/ig;

    # ���L�ǉ�or�폜
    foreach(@dids){
	if ( defined($date{$_}) ){ # ���O�ɏ�������Ă�����ǉ�
	    $bndate{$_} =$date{$_};
	    $bntitle{$_}=$title{$_};
	    $bnbody{$_} =$body{$_};
	} else { # ���O�ɏ�������ĂȂ���΍폜
	    delete $bndate{$_};
	}
    }

    #
    # (5)���L�t�@�C�����쐬����
    #

    # �쐬�O�Ƀt�@�C������������
    $existbefore=1 if (-e "$dir/$file");

    # �t�@�C���폜or�쐬
    if (scalar(keys %bndate) > 0){ # ���L������΍쐬
	open(FH,">$dir/$file")
	    || &error("���L�t�@�C�� $dir/$file �ɏ������߂܂���B");

	# head���쐬
	print FH $tmpbnhead;

	# ���t�Ń\�[�g
	@k=&SortedDID(*bndate);
	@k=reverse(@k) if ($tmpbnrev==1);

	# body���쐬
	foreach(@k){
	    print FH qq(<a name="$bndate{$_}"></a><a name="$_"></a>);
	    print FH "<!--akiary_diary did=$_ date=$bndate{$_}-->";
	    $tmp=$tmpbnbody;
	    # ���t
	    $dates=&date2sdate($bndate{$_});
	    $w3cdtf=&date2sdate($bndate{$_}, '%Y0-%M1-%D1', 1);
	    $tmp=~s/<!--\s*akiary_date\s*-->/$dates/g;
	    $tmp=~s/<!--\s*akiary_w3cdtf\s*-->/$w3cdtf/g;
	    # �^�C�g��
	    $tmp=~s/<!--\s*akiary_title\s*-->/<!--akiary_title-->$bntitle{$_}<!--\/akiary_title-->/;
	    $tmp=~s/<!--\s*akiary_title_2\s*-->/$bntitle{$_}/g;
	    # ���L�{��
	    $tmp=~s/<!--\s*akiary_body\s*-->/<!--akiary_body-->$bnbody{$_}<!--\/akiary_body-->/;
	    # ��did
	    $tmp =~ s/<!--\s*akiary_did\s*-->/$_/g;
	    # Permalink
		$bn_file = $bndate{$_};
		$bn_file =~ s/^(\d{6}).*/$1.html/;
		$base_uri = diary_dir_uri();
		$permalink = $base_uri . $bn_file . '#' . $_;
	    $tmp =~ s/<!--\s*akiary_link\s*-->/$permalink/g;

	    print FH "$tmp";
	    print FH "<!--/akiary_diary-->\n";
	}

	# foot���쐬
	print FH $tmpbnfoot;

	close(FH);
    } else { # ���L���Ȃ��ꍇ
	unlink("$dir/$file");
    }

    # �쐬��Ƀt�@�C�����ł�����
    $existafter=1 if (-e "$dir/$file");

    #
    # (6)�t�@�C�����b�N����
    #

    &my_funlock(*lfh); # ���b�N����

    #
    # (7)�K�v�Ȃ�ΐ挎����ї����̃t�@�C������X�V����
    #

    if ($existbefore!=$existafter){ # �V�K�쐬�������͍폜���ꂽ�Ƃ�
	# �挎�ւ̃����N�������ė����̃t�@�C���������
	if ($akiary_prevmonth==1 && $nextmonth ne $CFG{'next_month'}){
	    &MakeBNDiary($dir,$nextmonth,'','','','');
	}
	# �挎�ւ̃����N�������ė����̃t�@�C���������
	if ($akiary_nextmonth==1 && $prevmonth ne $CFG{'prev_month'}){
	    &MakeBNDiary($dir,$prevmonth,'','','','');
	}
    }
}

#
# �O��Ǝ���̃t�@�C����T��
#
sub GetPNFile{
    local($dir,$file)=@_;
    local(@files);
    local($prev,$next);

    opendir(DIR,$dir) || &error("���L�f�B���N�g���u$dir�v���J���܂���B");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    $prev=$CFG{'prev_month'};
    $next=$CFG{'next_month'};

    foreach(@files){
	if ($file gt $_){
	    $prev=$_;
	}
	if ($file lt $_){
	    $next=$_;
	    last;
	}
    }

    ($prev,$next);
}

#
# ���t��DID(Diary ID)�Ŕ�r����\�[�g�p�֐�
#

sub SortedDID{
    local(*date)=@_;
    local(%time);

    foreach (keys %date){
	$time{$_}=(split(/_/))[1];
    }

    sort {$date{$a}<=>$date{$b} || $time{$a}<=>$time{$b}} keys %date;
}


#
# �I�v�V���i�����L�t�@�C���쐬
# �y�����z
#   $tmpfile: �I�v�V���i�����L�e���v���[�g�t�@�C��
#   $outfile: �I�v�V���i�����L�t�@�C��
# �y����z
#   1. �e���v���[�g�t�@�C����ϐ��ɓǂݍ���
#   2. �ϐ�����<!-- akiary_\w+ -->�^�O��K�؂ɒu������
#   3. �ϐ����o�̓t�@�C���ɏ�������
#

sub MakeOptDiary{
    local($tmpfile,$outfile)=@_;

    local($file);
    local($prematch,$match,$postmatch);
    local($latest_times)=$CFG{'latest_times'};
    local(@files);
    local($lastmonth,$thismonth);
    local($y,$m);
    local(@m2,@m3,$tmp);
    local(%index,$index);

    #
    # 1. �e���v���[�g�t�@�C����ϐ��ɓǂݍ���
    #
    open(FH,$tmpfile)
	|| &error("�I�v�V���i�����L�̃e���v���[�g�t�@�C�� $tmpfile ���J���܂���B");
    $file=join("",<FH>);
    close(FH);

    #
    # 2. �ϐ�����<!-- akiary_.+ -->�^�O��K�؂ɒu������
    #

    # <!-- akiary_diary -->����<!-- /akiary_diary -->��u��
    if ($file=~/<!--\s*akiary_diary\s+[^>]*-->[\000-\377]*<!--\s*\/akiary_diary\s*-->/){
	# (1)�J�n�^�O�ȑO(2)�J�n�^�O����I���^�O�܂�(3)�I���^�O�ȍ~�ɕ���
	$prematch=$`;
	$match=$&;
	$postmatch=$';

	# (2)�J�n�^�O����I���^�O�܂ł���L�ɒu��
	($match,$latest_times)=&AkiaryDiaryTag2Diary(*CFG,$match);

	# (1)(2)(3)���Č���
	$file=$prematch . $match . $postmatch;
    }

    # <!-- akiary_latest_times -->��u��
    $file =~ s/<!--\s*akiary_latest_times\s*-->/$latest_times/g;

    # <!-- akiary_lastmonth -->
    # <!-- akiary_thismonth -->
    # <!-- akiary_index --> �̒u���̏���
    opendir(DIR,$CFG{'diary_dir'})
	    || &error("���L�f�B���N�g���u$CFG{'diary_dir'}�v���J���܂���B");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    # �I�v�V���i�����L�t�@�C��������L�t�@�C���ւ̑��΃p�X�����߂�
    local($rp,$optdir);
    ($optdir=$outfile)=~s|[^/]*$||;
    $rp=&RelativePath($optdir,$CFG{'diary_dir'});
    unless(defined($rp)){
	&error("�I�v�V���i�����L�t�@�C���u$outfile�v������L�f�B���N�g���u$CFG{'diary_dir'}�v�ւ̑��΃p�X�����߂��܂���B");
    }
    $rp.='/' if ($rp ne '');

    # <!-- akiary_lastmonth -->��<!-- /akiary_lastmonth -->��u��
    $lastmonth=$files[$#files];
    if ($lastmonth ne ""){
	$file =~ s/<!--\s*akiary_lastmonth\s*-->/<a href="$rp$lastmonth">/ig;
	$file =~ s/<!--\s*\/akiary_lastmonth\s*-->/<\/a>/ig;
    }

    # <!-- akiary_thismonth -->����<!-- /akiary_thismonth -->��u��
    ($y,$m)=&get_todays_date;
    $thismonth=sprintf("%04d%02d.html",$y,$m);
    ($thismonth)=grep(/^$thismonth$/,@files);
    if ($thismonth ne ""){
	$file =~ s/<!--\s*akiary_thismonth\s*-->/<a href="$rp$thismonth">/ig;
	$file =~ s/<!--\s*\/akiary_thismonth\s*-->/<\/a>/ig;
    }

    # <!-- akiary_index -->��u��
    if ($file =~ /<!--\s*akiary_index\s*-->/i){
	# ������ϊ��̏���
	@m2=('Jan','Feb','Mar','Apr','May','Jun',
	     'Jul','Aug','Sep','Oct','Nov','Dec');
	@m3=('January','February','March','April','May','June',
	     'July','August','September','October','November','December');
	# �e���ւ̃����N���������Ԃ𖄂߂���
	@files = reverse @files if ($CFG{'index_format_rev_month'} == 1);
	foreach (@files){
	    ($y,$m) = (/^(\d{4})(\d{2})/);
	    $tmp = $CFG{'index_format_month'};
	    $tmp =~ s/%Y0/$y/g;                      # 4������
	    $tmp =~ s/%Y1/sprintf("%02d",$y%100)/eg; # 2������
	    $tmp =~ s/%Y2/$y-1988/eg;                # ����
	    $tmp =~ s/%M0/sprintf("%d",$m)/eg;   # ��
	    $tmp =~ s/%M1/sprintf("%02d",$m)/eg; # ��(0�t��)
	    $tmp =~ s/%M2/$m2[$m-1]/g;          # ��(�p��Z�k)
	    $tmp =~ s/%M3/$m3[$m-1]/g;          # ��(�p��)
	    if (defined($index{$y})){
		$index{$y} .= $CFG{'index_format_between_months'};
	    }
	    $index{$y} .= "<a href=\"$rp$_\">$tmp</a>";
	}

	# �e�N����ꂽ��
	$index = '';
	@y = sort keys %index;
	@y = reverse @y if ($CFG{'index_format_rev_year'} == 1);
	foreach $y (@y){
	    $tmp = $CFG{'index_format_begin'};
	    $tmp =~ s/%Y0/$y/g;                      # 4������
	    $tmp =~ s/%Y1/sprintf("%02d",$y%100)/eg; # 2������
	    $tmp =~ s/%Y2/$y-1988/eg;                # ����
	    $index .= $tmp . $index{$y} . $CFG{'index_format_end'};
	}

	# �u��
	$file =~ s/<!--\s*akiary_index\s*-->/$index/ig;
    }

    # </body>�̒��O��$SIGNATURE��}��
    $file =~ s/<\/body>/$SIGNATURE\n<\/body>/ig; # �����}��

    #
    # 3. �ϐ����o�̓t�@�C���ɏ�������
    #
    open(FH,">$outfile")
	|| &error("�I�v�V���i�����L�t�@�C�� $outfile �ɏ������߂܂���B");
    print FH $file;
    close(FH);
}

#
# <!-- akiary_diary [^>]*-->����<!-- /akiary_diary -->����L�ɒu��
#

sub AkiaryDiaryTag2Diary{
    local(*CFG,$match)=@_;
    local($option,$reverse,$latest_times);
    local(@files,$file,$contents);
    local(%date,%title,%body);
    local(@k,$ret,$tmp);

    #
    # (1)akiary_diary�^�O���
    #
    $match =~ /<!--\s*akiary_diary\s+([^>]*)\s*-->([\000-\377]*)<!--\s*\/akiary_diary\s*-->/;
    $option = $1;
    $match = $2;  # �J�n�^�O�ƏI���^�O������

    # reverse or not
    $reverse = 1 if ($option =~ /reverse/i);

    # latest_times
    $latest_times = $CFG{'latest_times'};
    if ($option =~ /latest_times\s*=\s*"(\d+)"/){
	$latest_times = $1;
    }

    #
    # (2)���L�t�@�C����ǂ�
    #
    opendir(DIR,$CFG{'diary_dir'})
	|| &error("���L�f�B���N�g���u$CFG{'diary_dir'}�v���J���܂���B");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    foreach $file (reverse @files){
	open(FH,"$CFG{'diary_dir'}/$file")
	    || &error("���L�t�@�C���u$CFG{'diary_dir'}/$file�v���J���܂���B");
	$contents = join("",<FH>);
	close(FH);
	# ���L����؂�o���ADID�ADATE�ATITLE�ABODY���o
	&Contents2DTB($contents,*date,*title,*body);
	last if (scalar(keys %date) >= $latest_times);
    }

    #
    # (3)�ŐV�œ��L��ϐ���ō쐬
    #

    @k=&SortedDID(*date);
    $latest_times = $#k + 1 if ($latest_times > $#k);
    @k=splice(@k,-$latest_times,$latest_times);
    @k=reverse(@k) if ($reverse==1);
    foreach(@k){
	$ret .= qq(<a name="$date{$_}"></a><a name="$_"></a>);
	$tmp=$match;
	# ���t
	$dates=&date2sdate($date{$_});
	$w3cdtf=&date2sdate($date{$_}, '%Y0-%M1-%D1', 1);
	$tmp=~s/<!--\s*akiary_date\s*-->/$dates/g;
	$tmp=~s/<!--\s*akiary_w3cdtf\s*-->/$w3cdtf/g;
	# �^�C�g��
	$tmp=~s/<!--\s*akiary_title\s*-->/$title{$_}/;
	$tmp=~s/<!--\s*akiary_title_2\s*-->/$title{$_}/g;
	# ���L�{��
	$tmp=~s/<!--\s*akiary_body\s*-->/$body{$_}/;
	# ��did
	$tmp =~ s/<!--\s*akiary_did\s*-->/$_/g;
	# Permalink
	$bn_file = $date{$_};
	$bn_file =~ s/^(\d{6}).*/$1.html/;
	$base_uri = diary_dir_uri();
	$permalink = $base_uri . $bn_file . '#' . $_;
	$tmp =~ s/<!--\s*akiary_link\s*-->/$permalink/g;

	$ret.=$tmp;
    }

    return($ret,$latest_times);
}

#
# &RelativePath($fromdir,$todir)
#   �f�B���N�g���p�X$fromdir����f�B���N�g���p�X$todir�ւ̑��΃p�X��Ԃ�
#   (��)&RelativePath("a/b/c" ,"a/b/d" ) -> "../d"
#       &RelativePath("a/b/c" ,"d/e/f" ) -> "../../../d/e/f"
#       &RelativePath("a/b/c" ,"a"     ) -> "../.."
#       &RelativePath("/a/b/c","/a/b/d") -> "../d"
#       &RelativePath("/a/b/c","a/b/d" ) -> undef
#
sub RelativePath {
    # ��΃p�X�Ƒ��΃p�X�Ƃ̑��΃p�X�͋��߂��Ȃ�
    if ( ($_[0] =~ m|^/| && $_[1] !~ m|^/|) ||
	 ($_[0] !~ m|^/| && $_[1] =~ m|^/|) ){
	return;
    }
    # �������e�f�B���N�g���ɕ���(�u//�v�u./�v�͏���)
    local(@fromdirs)=grep(!/^\.?$/,split('/',$_[0]));
    local(@todirs)  =grep(!/^\.?$/,split('/',$_[1]));
    # ���ʃp�X������
    while($fromdirs[0] eq $todirs[0]){
	last unless shift(@fromdirs);
	last unless shift(@todirs);
    }
    # $fromdir����e�f�B���N�g���Ɉړ�
    while(shift(@fromdirs)){
	unshift(@todirs,'..');
    }
    # ���΃p�X��Ԃ�
    join('/',@todirs);
}

#
# �u&<>"�v���G�X�P�[�v����
#
sub escapeHTML{
    local($str)=@_;
    $str=~s/&/&amp;/g;
    $str=~s/</&lt;/g;
    $str=~s/>/&gt;/g;
    $str=~s/\"/&quot;/g;
    return($str);
}

#
# ���t������L�t�@�C�����ɕϊ�
#
# �y�ݒ�z$CFG{'dfile_div_mday'}: ���L�t�@�C���𕪊������
# �y�����z$date: yyyymmdd�`���̓��t
# �y�Ԓl�z$dfn: yyyymm.html�����yyyymmdd.html�`���̓��L�t�@�C����
#
# ��)$CFG{'dfile_div_mday'} eq ''
#      &date2dfn('20020327') -> '200203.html'
#    $CFG{'dfile_div_mday'} eq '1 16'
#      &date2dfn('20020327') -> '20020316.html'
#    $CFG{'dfile_div_mday'} eq '1 11 21'
#      &date2dfn('20020327') -> '20020321.html'
#
sub date2dfn{
    local($date)=@_;
    local(@div_date);

    # ���������������Ƃ��͂��̂܂�return
    (local($y,$m,$d)=($date=~/(\d{4})(\d{2})(\d{2})/)) || return;

    # $CFG{'dfile_div_mday'}�Ɏw�肪�Ȃ��Ƃ���yyyymm.html�`����Ԃ�
    (@div_date=split(' ',$CFG{'dfile_div_mday'})) || return("$y$m.html");

    # $CFG{'dfile_div_mday'}�Ɏw�肪����Ƃ�
    foreach ( reverse(sort(@div_date)) ){
	if ($_ <= $d){
	    return( sprintf("%04d%02d%02d.html",$y,$m,$_) );
	}
    }
    return("$y${m}01.html");
}

sub diary_dir_uri {
	my $uri = $ENV{'SCRIPT_NAME'};
	$uri =~ s!^(.*?)(?:[\./]+?)(?:\w+\.cgi|/)$!$1!;
	return 'http://' . $ENV{'HTTP_HOST'} . $uri . '/' . (($dcfg->{'diary_dir'} eq './') ? '' : $dcfg->{'diary_dir'});
}
