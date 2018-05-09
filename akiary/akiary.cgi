#! /usr/local/bin/perl
#
# akiary - Y.Akira's Diary CGI
#   Copyright (C) 2000-2005 by YAMAMOTO Akira
#   mailto:yakira at hi-ho.ne.jp
#   http://www.hi-ho.ne.jp/yakira/akiary/
#

# バージョン
my $VERSION="0.61"; # 2005/03/29

# パラメータ解析
my %FORM=&parse_param;

# akiary設定
my $akiary_cfg_file='cfg/akiary.cfg';
my $acfg=
  {
   user_cfg_file=>{''=>'cfg/user.cfg'},
   time_zone=>'+0900',
   newline => '<br>',
   charset => 'SHIFT_JIS',
  };
&parse_cfg_file($akiary_cfg_file,$acfg);

# ユーザ設定
my $ucfg=
  {
   password=>'',
   diary_cfg_file=>{''=>'cfg/diary.cfg'},
  };
&parse_cfg_file($acfg->{'user_cfg_file'}->{&param('user')},$ucfg);

# 日記設定
my $dcfg=
  {
   # 日記テンプレートファイル
   'diary_tmp_file'=>'./tmpbn.html',
   # 日記ディレクトリ
   'diary_dir'=>'./',
   # ロックファイルのディレクトリ
   'lock_dir'=>'./',
   # オプショナル日記のテンプレートファイルと出力ファイル
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
   # このスクリプトから見た日記のディレクトリ
   'diary_url'=>'./index.html',
   # 最新n回分(latest n times)
   'latest_times'=>'7',
   # 先月のバックナンバーがない場合のリンク先
   'prev_month'=>'',
   # 来月のバックナンバーがない場合のリンク先
   'next_month'=>'',
   # 日記入力時の題名の枠の長さ
   'form_title_size'=>'40',
   # 日記入力時の内容の枠の大きさ(列)
   'form_body_cols'=>'80',
   # 日記入力時の内容の枠の大きさ(行)
   'form_body_rows'=>'10',
   # 日付表示フォーマット
   'date_format'=>'%Y0年%M0月%D0日(%W0)',
   # 日付の色のタグ('font' or 'span')
   'date_color_tag'=>'span',
   # 目次フォーマット: 各年の始め
   'index_format_begin'=>'%Y0年 [ ',
   # 目次フォーマット: 各月
   'index_format_month'=>'%M0月',
   # 目次フォーマット: 各月の間
   'index_format_between_months'=>' | ',
   # 目次フォーマット: 各年の終わり
   'index_format_end'=>' ]<br>',
   # 目次フォーマット: 年の順番(0:昇順、1:降順)
   'index_format_rev_year'=>'1',
   # 目次フォーマット: 月の順番(0:昇順、1:降順)
   'index_format_rev_month'=>'0',
   # ファイル分割日
   'dfile_div_mday'=>'',
  };
&parse_cfg_file($ucfg->{'diary_cfg_file'}->{param('diary')},$dcfg);

# v.0.51を全面修正せずに済ませるための変換
my %CFG;
for (keys %{$dcfg}) {
    $CFG{$_}=$dcfg->{$_};
}

# スクリプトのURL
my $relative_url=$0;
$relative_url=~s/.*[\\\/]//; # パス除去
my $relative_url_with_query=$relative_url;
$relative_url_with_query.='?'.$ENV{'QUERY_STRING'} if ($ENV{'QUERY_STRING'});
my $OWNFILE=$relative_url_with_query; # v.0.51との互換性のため

# クレジット(<a>から</a>までは変更不可)
my $SIGNATURE = <<"_SIGNATURE_";
<div style="text-align:center;">
<a href="http://www.hi-ho.ne.jp/yakira/akiary/" target="akiary">Akiary v.$VERSION</a>
</div>
_SIGNATURE_

# パスワード処理
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
# 処理実行
#
if ($FORM{'action'} eq "append"){      # 更新
    &Append;
} elsif ($FORM{'action'} eq "modify"){ # 修正
    &Modify;
} elsif ($FORM{'action'} eq "delete"){ # 削除
    &Delete;
}

#
# ページ表示
#
if ($FORM{'page'} eq "now"){ # 新規
    &PageNow;
} elsif ($FORM{'page'} eq "bn"){ # バックナンバー
    &PageBacknumber;
} elsif ($FORM{'page'} eq "modify"){ # 修正
    &PageModify;
} elsif ($FORM{'page'} eq "deleteYN"){ # 削除確認
    &PageDeleteYN;
} else { # パスワード入力
    &display_password_entry_page;
}

exit;

#----------------
# パスワード認証
#----------------

sub auth_password {
    my $cpw=$ucfg->{'password'};
    my $ppw=param('password');

    # $cpw eq ''のときは常にcrypt比較が真になってしまうので、
    # $cpw ne ''を条件に付加している。
    if ($cpw ne '' && crypt($ppw,$cpw) eq $cpw) {
	return 1;
    }
    return 0;
}

#
# パスワード設定
#

sub set_password {
    my $user_cfg_file=$acfg->{'user_cfg_file'}->{param('user')};
    # * 動作を決める条件
    # ユーザ設定ファイルが存在するか?
    my $du=(-f $user_cfg_file);
    # 新しいパスワードが入力されているか?
    my $pn=(defined(param('new_password'))
	    || defined(param('re_enter_new_password')));
    # パスワード設定済か?
    my $up=($ucfg->{'password'} ne '');
    # パスワードが正しいか?
    my $ap=&auth_password;
    # 2つの新しいパスワードが同じか?
    my $mc=(param('new_password') eq param('re_enter_new_password'));

    # * 真理値表
    # ua:unauth(パスワード認証失敗)
    # um:unmatch(2つの新しいパスワードが同じでない)
    # sc:success(パスワード設定条件を満たす)
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

    # パスワードを暗号化してファイルに書き込む
    if ($res->{'success'}==1) {
	my $salt=join '',('.','/',0..9,'A'..'Z','a'..'z')[rand 64,rand 64];
	my $crypted_password=crypt(&param('new_password'),$salt);
	my($sec,$min,$hour,$mday,$mon,$year)=&my_gmtime;
	my $t=sprintf("%d/%02d/%02d %02d:%02d:%02d",
		      $year+1900,$mon+1,$mday,$hour,$min,$sec);
	open(FH,">>$user_cfg_file") or
	  &error('ユーザ設定ファイル"'.$user_cfg_file.'"に書き込めません。');
	print FH '# by "'.&param('user').'" '.
	  'from '.$ENV{REMOTE_ADDR}.' at '.$t."\n";
	print FH 'password="'.$crypted_password."\"\n";
	close(FH);
    }

    return($res);
}

#
# time()を人間がわかりやすい時刻表示に変換する。
# その際、akiary設定でのtime_zoneを考慮する。
#

sub my_gmtime{
    my($pm,$h,$m) = ($acfg->{'time_zone'} =~ /([+-])(\d\d):?(\d\d)/);
    my $time_offset = $h * 3600 + $m * 60;
    $time_offset *= (-1) if ($pm eq '-');
    gmtime(time + $time_offset);
}

#----------
# 処理実行
#----------

#
# 更新
#
sub Append{
    local($date,@dids);
    local(*DATE,*TITLE,*BODY);
    local($file);
    local($tmp,$out);

    # 更新実行
    $date=sprintf("%04d%02d%02d",$FORM{'year'},$FORM{'mon'},$FORM{'mday'});
    $dids[0]=$date."_".time;
    $DATE{$dids[0]}=$date;
    $TITLE{$dids[0]}=$FORM{'title'};
    $BODY{$dids[0]}=$FORM{'body'};
    $BODY{$dids[0]}=~s/\x0D\x0A/\n/g; # 改行コード変換(Win)
    $BODY{$dids[0]}=~s/\x0D/\n/g;     # 改行コード変換(Mac)
    $BODY{$dids[0]}=~s/\x0A/\n/g;     # 改行コード変換(UNIX)
    $newline = $acfg->{newline};
    $newline =~ s/\\n/\n/g;
    $BODY{$dids[0]} =~ s/\n/$newline/g;

    $file=&date2dfn($date);

    &MakeBNDiary($CFG{'diary_dir'},$file,*DATE,*TITLE,*BODY,*dids);

    # オプショナル日記ファイルを作成
    foreach $tmp (grep(/^opt_diary_tmp_file_\d+$/,(keys %CFG))){
	$out=$tmp;
	$out=~s/tmp_//;
	next if ($CFG{$tmp} eq "");
	&MakeOptDiary($CFG{$tmp},$CFG{$out});
    }
}

#
# 修正
#
sub Modify{
    local(@dids,$date);
    local(*DATE,*TITLE,*BODY);
    local($file);
    local($tmp,$out);

    # 更新実行
    $dids[0]=$FORM{'did'};
    $date=sprintf("%04d%02d%02d",$FORM{'year'},$FORM{'mon'},$FORM{'mday'});
    $DATE{$dids[0]}=$date;
    $TITLE{$dids[0]}=$FORM{'title'};
    $BODY{$dids[0]}=$FORM{'body'};
    $BODY{$dids[0]}=~s/\x0D\x0A/\n/g; # 改行コード変換(Win)
    $BODY{$dids[0]}=~s/\x0D/\n/g;     # 改行コード変換(Mac)
    $BODY{$dids[0]}=~s/\x0A/\n/g;     # 改行コード変換(UNIX)
    $newline = $acfg->{newline};
    $newline =~ s/\\n/\n/g;
    $BODY{$dids[0]} =~ s/\n/$newline/g;

    $file=&date2dfn($date);

    &MakeBNDiary($CFG{'diary_dir'},$file,*DATE,*TITLE,*BODY,*dids);

    # バックナンバー間移動した場合は前のファイルから消す
    # (例)2000年1月1日のを1999年12月31日に修正した場合、200001.htmlから消す
    if ($file ne $FORM{'dfn'}){
	&MakeBNDiary($CFG{'diary_dir'},$FORM{'dfn'},'','','',*dids);
    }

    # オプショナル日記ファイルを作成
    foreach $tmp (grep(/^opt_diary_tmp_file_\d+$/,(keys %CFG))){
	$out=$tmp;
	$out=~s/tmp_//;
	next if ($CFG{$tmp} eq "");
	&MakeOptDiary($CFG{$tmp},$CFG{$out});
    }

    # 修正後画面で「そのまま」を選択したときにはファイル名を変更
    if ($FORM{'page'} eq 'modify'){
	$FORM{'dfn'}=$file;
    }
}

#
# 削除
#
sub Delete{
    local(@dids);
    local($tmp,$out);

    $dids[0]=$FORM{'did'};

    # 削除
    &MakeBNDiary($CFG{'diary_dir'},$FORM{'dfn'},'','','',*dids);

    # オプショナル日記ファイルを作成
    foreach $tmp (grep(/^opt_diary_tmp_file_\d+$/,(keys %CFG))){
	$out=$tmp;
	$out=~s/tmp_//;
	next if ($CFG{$tmp} eq "");
	&MakeOptDiary($CFG{$tmp},$CFG{$out});
    }
}


#------------
# ページ表示
#------------

#
# パスワード入力ページ表示
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

    my $html=&HtmlHeader('パスワード入力');
    $html.=<<'_END_OF_HTML_';
<hr>
<TMPL_IF NAME="password_entry">
<p>パスワードが違います。</p>
</TMPL_IF>
<form method="POST" action="<TMPL_VAR NAME="url">">
<input type="hidden" name="page" value="now">
パスワード
<input type="password" name="password">
<input type="submit" value="入力">
<input type="reset" value="取消">
</form>
_END_OF_HTML_
    $html.=&HtmlFooter;
    &PrintHTTP(&template_output($html,$p));
}

#
# パスワード設定ページ表示
#

sub display_password_setting_page {
    my $p=shift;
    $p->{'url'}=$relative_url_with_query;
    $p->{'url_nocmd'}=$relative_url_with_query;
    $p->{'url_nocmd'}=~s/cmd=set_password//;
    if ($ucfg->{'password'} ne '') {
	$p->{'password_defined'}=1;
    }

    my $html=&HtmlHeader('パスワード設定');
    $html.=<<'_END_OF_HTML_';
<hr>
<TMPL_IF NAME="unauth">
 <h2>メッセージ</h2>
 <p>パスワードが異なります。もう一度入力して下さい。</p>
</TMPL_IF>

<TMPL_IF NAME="unmatch">
 <h2>メッセージ</h2>
 <p>
  新しいパスワードと確認用の新しいパスワードが異なります。
  もう一度入力して下さい。
 </p>
</TMPL_IF>

<TMPL_IF NAME="success">
 <h2>メッセージ</h2>
 <p>パスワードを設定しました。</p>
 <p>続けて日記を書くときは、
  <a href="<TMPL_VAR NAME="url_nocmd">"><TMPL_VAR NAME="url_nocmd"></a>
  をクリックして下さい。
 </p>
</TMPL_IF>

<h2>新パスワード入力</h2>
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
    <input type="submit" value="入力">
    <input type="reset" value="取消">
   </td>
 </table>
</form>
_END_OF_HTML_
    $html.=&HtmlFooter;
    &PrintHTTP(&template_output($html,$p));
}

#
# 簡易版HTML::Template->output
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
# 新規画面表示
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

    # 日記ファイル名取得
    opendir(DIR,$CFG{'diary_dir'})
	|| &error("日記ディレクトリ $CFG{'diary_dir'} が開けません。");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    # 日記ファイルを読む
    foreach $file (reverse(@files)){
	open(FILE,"$CFG{'diary_dir'}/$file")
	    || &error("日記ファイル $CFG{'diary_dir'}/$file が開けません。");
	$contents=join("",<FILE>);
	close(FILE);
	# 日記部を切り出し、DID、DATE、TITLE、BODY抽出
	&Contents2DTB($contents,*date,*title,*body);
	# 各DIDの日記ファイル名
	foreach(keys %date){
	    $dfn{$_}=$file unless defined($dfn{$_});
	}
	# 規定数集めたら終わり
	last if (scalar(keys %date)>=$CFG{'latest_times'});
    }

    #
    # 表示準備
    #
    $html=&HtmlHeader("新規");
    $html.=<<"_HTML_";
<hr>
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="append">
_HTML_
    # 日記入力テーブル表示
    %tmp=("year",$syear, "mon",$smon, "mday",$smday,
	  "rows",$CFG{'form_body_rows'}, "cols",$CFG{'form_body_cols'},
	  "size",$CFG{'form_title_size'}, "submit","新規");
    $html.=&DiaryInputTable(*tmp);
    $html.=<<"_HTML_";
<input type="hidden" name="page" value="now">
</form>
_HTML_

    # 修正/削除
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
<input type="radio" name="page" value="modify" checked>修正
<input type="radio" name="page" value="deleteYN">削除
<input type="hidden" name="dfn" value="$dfn{$_}">
<input type="hidden" name="did" value="$_">
<input type="hidden" name="retpage" value="now">
<input type="submit" value="入力">
</form>
_HTML_
	}
    }

    # ファイル選択
    if (@files){
	$html.="<hr>\n";
	$html.=&HtmlFileSelect($files[-1],@files);
    }

    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# バックナンバー画面表示
#
sub PageBacknumber{
    local($contents);
    local(*date,*title,*body);
    local($escpw)=&escapeHTML($FORM{'password'});

    # ページ表示
    local($html)=&HtmlHeader("バックナンバー$FORM{'dfn'}");
    $html.="<hr>\n";

    # ファイル読み込み
    open(FH,"$CFG{'diary_dir'}/$FORM{'dfn'}")
	|| ($html.="<p>$FORM{'dfn'}はありません。</p>\n");
    $contents=join("",<FH>);
    close(FH);

    # 日記ファイル解析
    &Contents2DTB($contents,*date,*title,*body);

    # バックナンバー一覧
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
<input type="radio" name="page" value="modify" checked>修正
<input type="radio" name="page" value="deleteYN">削除
<input type="hidden" name="retpage" value="bn">
<input type="submit" value="入力">
</form>
_HTML_
    }

    # 新規画面へ
    $html.=<<"_HTML_";
<hr>
<form method="post" action="$OWNFILE">
<input type="hidden" name="password" value="$escpw">
<input type="hidden" name="action" value="noop">
<input type="hidden" name="page" value="now">
<input type="submit" value="新規画面へ">
</form>
_HTML_

    # 日記ファイル名取得
    opendir(DIR,$CFG{'diary_dir'})
	|| &error("日記ディレクトリ $CFG{'diary_dir'} が開けません。");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);
    $html.=&HtmlFileSelect($FORM{'dfn'},@files);

    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# 修正表示
#
sub PageModify{
    local($contents);
    local(*date,*title,*body);
    local($syear,$smon,$smday);
    local($html);
    local($escpw)=&escapeHTML($FORM{'password'});
    local(%tmp);

    # ファイル読み込み
    open(FILE,"$CFG{'diary_dir'}/$FORM{'dfn'}")
	|| &error("日記ファイル「$CFG{'diary_dir'}/$FORM{'dfn'}」が開けません。");
    $contents=join("",<FILE>);
    close(FILE);

    # 日記ファイル解析
    &Contents2DTB($contents,*date,*title,*body);

    # 更新/削除
    ($date,$title,$body)
	=($date{$FORM{'did'}},$title{$FORM{'did'}},$body{$FORM{'did'}});
    ($syear,$smon,$smday)=($date=~/^(\d{4})(\d{2})(\d{2})/);
	if ($acfg->{newline} eq '<br>') {
	    $body=~tr/\x0D\x0A//d; # 改行コード削除
	    $body=~s/<br>/\n/ig;
	}

    # ページ表示
    $html=&HtmlHeader("修正");
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
	  "title",$title, "body",$body, "submit","修正");
    $html.=&DiaryInputTable(*tmp);

    $html.=<<"_HTML_";
<p>
修正後画面
<input type="radio" name="page" value="modify" checked>そのまま
<input type="radio" name="page" value="$FORM{'retpage'}">もどる
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
<input type="submit" value="もどる">
</form>
</center>
_HTML_

    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# 削除確認画面表示
#
sub PageDeleteYN{
    local($contents);
    local(*date,*title,*body);
    local($sdate);
    local($html);
    local($escpw)=&escapeHTML($FORM{'password'});

    # ファイル読み込み
    open(FILE,"$CFG{'diary_dir'}/$FORM{'dfn'}")
	|| &error("日記ファイル「$CFG{'diary_dir'}/$FORM{'dfn'}」が開けません。");
    $contents=join("",<FILE>);
    close(FILE);

    # 日記ファイル解析
    &Contents2DTB($contents,*date,*title,*body);

    $sdate=&date2sdate($date{$FORM{'did'}});
    $title=&escapeHTML($title{$FORM{'did'}});
    $body=$body{$FORM{'did'}};
    $body=&escapeHTML($body);
    $body=~s/&lt;br&gt;/<br>/ig;

    # 表示
    $html=&HtmlHeader("削除確認");
    $html.=<<"_HTML_";
<hr>
<p>削除してもよろしいですか？</p>
<table border="1">
 <tr>
  <th>日付</th>
  <td>$sdate</td>
 </tr>
 <tr>
  <th>題名</th>
  <td>$title</td>
 </tr>
 <tr>
  <th>内容</th>
  <td>$body</td>
 </tr>
</table>
<form method="post" action="$OWNFILE">
 <input type="hidden" name="password" value="$escpw">
 <input type="radio" name="action" value="delete">はい
 <input type="radio" name="action" value="noop" checked>いいえ
 <input type="hidden" name="dfn" value="$FORM{'dfn'}">
 <input type="hidden" name="did" value="$FORM{'did'}">
 <input type="hidden" name="page" value="$FORM{'retpage'}">
 <input type="submit" value="入力">
 <input type="reset" value="取消">
</form>
_HTML_
    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#----------------
# サブルーチン群
#----------------

#
# 設定ファイル解析
# 【引数】
#  $cfg_file: 設定ファイル名
#  $cfg: 設定用ハッシュ変数へのリファレンス
# 【注意】
#  設定ファイル名がNULL('')のときは即座にリターン。
#  すなわちプログラム中のデフォルト値が用いられる。
#  設定用ハッシュ変数$cfgは事前にデフォルト値を与える必要あり。
#  definedでない場合はエラーとなる。
#  $ENV{'xxx'}は展開可能(for Hi-HO)
#

sub parse_cfg_file ($$){
    my($cfg_file) = shift;
    my($cfg) = shift;

    return if ($cfg_file eq '');

    open(FH,$cfg_file) || &error('設定ファイル"'.$cfg_file.'"が開けません。');
    while(<FH>){
	next if (/^\s*$/);
	next if (/^#/);
	unless (/^(-)?(\w+)((?:\{"\w*"\}){0,2})\s*=\s*("[^"]*")/){
	    &error('設定ファイル'.$cfg_file.'の'.$..'行目が文法エラーです。');
	}
	my($k,$ke,$v)=($2,$3,$4);
	unless (defined($cfg->{$k})){
	    &error('設定ファイル'.$cfg_file.'の設定名'.$k.'は設定できません。'.
		   'akiary.cgiでデフォルト値を設定して下さい。');
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
# CGIのパラメータ(フォーム入力)のデコード
#   参考文献: Scott Guelich et al., "CGIプログラミング第2版", 4章3節, p.94.
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

    # akiaryタグの除去
    if ( $form_data{'title'} ){
	$form_data{'title'}=~s/<(!--\s*\/?akiary[^>]*)>/&lt;$1&gt;/ig
    }
    if ( $form_data{'body'} ) {
	$form_data{'body'}=~s/<(!--\s*\/?akiary[^>]*)>/&lt;$1&gt;/ig;
    }

    return %form_data;
}

#
# 将来CGI.pmを導入するための布石
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
# HTMLのヘッダー部
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
[<a href="$CFG{'diary_url'}" target="diary">日記</a>]
<div class="title">Akiary</div>
<div class="subtitle">$_[0]</div>
_HTML_
}

#
# HTMLのフッター部
#
sub HtmlFooter{
    return <<"_HTML_";
<hr>
$SIGNATURE</body>
</html>
_HTML_
}

#
# ファイル選択のHTML
# ・引数
#   $sfile: デフォルト選択のファイル名
#   @files: ファイル名
# ・返値
#   ファイル選択のHTML
#
sub HtmlFileSelect{
    local($sfile,@files)=@_;
    local($html);
    local($escpw)=&escapeHTML($FORM{'password'});

    # ファイルがなければ終わり
    return unless (@files);

    # ファイル選択HTML作成
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
<input type="submit" value="選択">
</form>
_HTML_
}

#
# 日付を数字から文字列に変換
# (例) 20001020 → <font color="#000000">2000年10月20日(金)</font>
# 【引数】
#  $date  : 数字の日付 
#  $format: フォーマット
#    %Y0 1900-9999
#    %Y1 00-99
#    %Y2 1-8011(平成元号)
#    %M0 1-12
#    %M1 01-12
#    %M2 Jan-Dec
#    %M3 January-December
#    %D0 1-31
#    %D1 01-31
#    %W0 日-土
#    %W1 Sun-Sat
#    %W2 Sunday-Saturday
#    デフォルトは"%Y0年%M0月%D0日(%W0)"
#
sub date2sdate{
    local($date,$format,$no_tag)=@_;
    local($y0,$m0,$d0,$w);
    local(@m2,@m3,@w0,@w1,@w2);
    local($color,$class,$sdate);

    $format=$CFG{'date_format'} if ($format eq "");

    # 年月日
    ($y0,$m0,$d0)=($date=~/(\d{4})(\d{2})(\d{2})/);
    $y0=1900 if ($y0 < 1900);
    $m0=1 if ($m0 < 1);
    $m0=12 if ($m0 > 12);
    $d0=1 if ($d0 < 1);
    $d0=31 if ($d0 > 31);

    # 曜日(0:日曜; 6:土曜)
    $w=&GetWdayZeller($y0,$m0,$d0);

    # 文字列変換の準備
    @m2=('Jan','Feb','Mar','Apr','May','Jun',
	 'Jul','Aug','Sep','Oct','Nov','Dec');
    @m3=('January','February','March','April','May','June',
	 'July','August','September','October','November','December');
    @w0=('日','月','火','水','木','金','土');
    @w1=('Sun','Mon','Tue','Wed','Thu','Fri','Sat');
    @w2=('Sunday','Monday','Tuesday','Wednesday',
	 'Thursday','Friday','Saturday');

    # 文字列日付
    $sdate=$format;
    $sdate=~s/%Y0/$y0/g;                      # 4桁西暦
    $sdate=~s/%Y1/sprintf("%02d",$y0%100)/eg; # 2桁西暦
    $sdate=~s/%Y2/$y0-1988/eg;                # 平成元号
    $sdate=~s/%M0/sprintf("%d",$m0)/eg;   # 月
    $sdate=~s/%M1/sprintf("%02d",$m0)/eg; # 月(0付き)
    $sdate=~s/%M2/$m2[$m0-1]/g;          # 月(英語短縮)
    $sdate=~s/%M3/$m3[$m0-1]/g;          # 月(英語)
    $sdate=~s/%D0/sprintf("%d",$d0)/eg;   # 日
    $sdate=~s/%D1/sprintf("%02d",$d0)/eg; # 日(0付き)
    $sdate=~s/%W0/$w0[$w]/g; # 曜日
    $sdate=~s/%W1/$w1[$w]/g; # 曜日(英語短縮)
    $sdate=~s/%W2/$w2[$w]/g; # 曜日(英語)

    if ($no_tag) {

    } elsif ($CFG{'date_color_tag'} eq 'font') {
	$color="#000000";              # 平日の色
	$color="#DD0000" if ($w == 0); # 日曜日の色
	$color="#3333FF" if ($w == 6); # 土曜日の色
	$sdate="<font color=\"$color\">$sdate</font>";
    } elsif ($CFG{'date_color_tag'} eq 'span') {
	$class="weekday";               # 平日の色
	$class="sunday"   if ($w == 0); # 日曜日の色
	$class="saturday" if ($w == 6); # 土曜日の色
	$sdate="<span class=\"$class\">$sdate</span>";
    }
    # リターン
    return $sdate;
}

#
# エラー
#
sub error{
    local($html)=&HtmlHeader("エラー");
    $html.="<hr>\n<p>@_</p>\n";
    $html.=&HtmlFooter;
    &PrintHTTP($html);
    exit;
}

#
# デバグ用
#
sub debug{
    local($html)=&HtmlHeader("デバグ");
    $html.="<hr>\n";
    $html.=&HtmlFooter;
    &PrintHTTP($html);
}

#
# 今日の年月日を得る
#

sub get_todays_date{
    my($pm,$h,$m)=($acfg->{'time_zone'}=~/([+-])(\d\d):?(\d\d)/);
    my $time_offset = $h*3600+$m*60;
    $time_offset *= (-1) if ($pm eq "-");
    my($mday,$mon,$year)=(gmtime(time+$time_offset))[3..5];
    return($year+1900,$mon+1,$mday);
}

#
# 日記ファイルの中身から、日付とタイトルと本文を抽出する
#

sub Contents2DTB{
    local($contents,*date,*title,*body)=@_;
    local($did,$tb,$d,$t,$b);

    # Perl4では「?」で最短一致させられないため以下のように処理
    while($contents=~/<!--\s*akiary_diary did=(\S+) date=(\d+)\s*-->/){
	($did,$d)=($1,$2);
	$contents=$'; # マッチした文字列より後の部分
	$contents=~/<!--\s*\/akiary_diary\s*-->/;
	$contents=$';
	$tb=$`; # <!--akiary_diary-->から<!--/akiary_diary-->まで
	($t)=($tb=~/<!--\s*akiary_title\s*-->([\000-\377]*)<!--\s*\/akiary_title\s*-->/);
	($b)=($tb=~/<!--\s*akiary_body\s*-->([\000-\377]*)<!--\s*\/akiary_body\s*-->/);
	$date{$did}=$d;
	$title{$did}=$t;
	$body{$did}=$b;
    }
}

#
# zellerの公式による曜日算出関数
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
# 日記テンプレートファイルを解析する
#

sub AnalyzeTmpbn{
    local(*contents,*head,*opt,*body,*foot)=@_;

    if ($contents=~/<!--\s*akiary_diary([^>]*)\s*-->([\000-\377]*)<!--\s*\/akiary_diary\s*-->/i){
	$head=$`; # ヘッダ部
	$opt=$1;  # akiary_diaryのオプション
	$body=$2; # akiary_diaryの本文
	$foot=$'; # フッタ部

	# (1)本文中にakiary_diaryタグがない
	# (2)本文中にakiary_titleタグはひとつのみ
	# (3)本文中にakiary_bodyタグはひとつのみ
	if ($body !~ /<!--\s*akiary_diary[^>]*\s*-->/i &&
	    $body !~ /<!--\s*\/akiary_diary\s*-->/i &&
	    ($body =~ s/<!--\s*akiary_title\s*-->/$&/ig) == 1 &&
	    ($body =~ s/<!--\s*akiary_body\s*-->/$&/ig) == 1) {
	    return(1); # 解析成功すれば1を返す
	}
    }
}

#
# 日記テンプレートファイルのエラー
#
sub ErrorTmpbn{
    local($html)=&HtmlHeader("日記テンプレートファイルのエラー");
    $html.=<<END_OF_TEXT;
<hr>
<p>
エラーの原因は以下の6点のいずれかです。<br>
<ol>
<li>「<tt>&lt;!--akiary_diary--&gt;</tt>」か「<tt>&lt;!--/akiary_diary--&gt;</tt>」がありません。
<li>「<tt>&lt;!--akiary_diary--&gt;</tt>」か「<tt>&lt;!--/akiary_diary--&gt;</tt>」が2つ以上あります。
<li>「<tt>&lt;!--akiary_diary--&gt;</tt>」と「<tt>&lt;!--/akiary_diary--&gt;</tt>」の間に「<tt>&lt;!--akiary_title--&gt;</tt>」がありません。
<li>「<tt>&lt;!--akiary_diary--&gt;</tt>」と「<tt>&lt;!--/akiary_diary--&gt;</tt>」の間に「<tt>&lt;!--akiary_title--&gt;</tt>」が2つ以上あります。
<li>「<tt>&lt;!--akiary_diary--&gt;</tt>」と「<tt>&lt;!--/akiary_diary--&gt;</tt>」の間に「<tt>&lt;!--akiary_body--&gt;</tt>」がありません。
<li>「<tt>&lt;!--akiary_diary--&gt;</tt>」と「<tt>&lt;!--/akiary_diary--&gt;</tt>」の間に「<tt>&lt;!--akiary_body--&gt;</tt>」が2つ以上あります。
</ol>
</p>
END_OF_TEXT
    $html.=&HtmlFooter;
    &PrintHTTP($html);
    exit;
}

#
# 日記入力テーブル表示
#
# 【引数】
#   $opt{"year"}  : デフォルト選択の年
#   $opt{"mon"}   : デフォルト選択の月
#   $opt{"mday"}  : デフォルト選択の日
#   $opt{"size"}  : 題名の長さ
#   $opt{"cols"}  : 内容の列数
#   $opt{"rows"}  : 内容の行数
#   $opt{"title"} : 題名
#   $opt{"body"}  : 内容
#   $opt{"submit"}: submitボタン
# 【返値】
#   日記入力テーブル(<TABLE>から</TABLE>まで)
#

sub DiaryInputTable{
    local(*opt)=@_;
    local($option0112,$option0131);
    local($title)=&escapeHTML($opt{"title"});
    local($body)=&escapeHTML($opt{"body"});

    # 月選択
    foreach(1..12){
	if ($_ == $opt{"mon"}){
	    $option0112.="<option value=\"$_\" selected>$_";
	} else {
	    $option0112.="<option value=\"$_\">$_";
	}
    }
    # 日選択
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
  <th>日付</th>
  <td>
   <input type="text" name="year" value="$opt{'year'}" size="4">年
   <select name="mon">$option0112</select>月
   <select name="mday">$option0131</select>日
  </td>
 </tr>
 <tr>
  <th>題名</th>
  <td>
   <input type="text" name="title" value="$title" size="$opt{'size'}">
  </td>
 </tr>
 <tr>
  <th>内容</th>
  <td>
   <textarea rows="$opt{'rows'}" cols="$opt{'cols'}" wrap="soft" name="body">$body</textarea>
  </td>
 </tr>
 <tr>
  <th></th>
  <td>
   <input type="submit" value="$opt{'submit'}">
   <input type="reset" value="取消">
  </td>
 </tr>
</table>
END_OF_TEXT
}

#
# rename方式ファイルロック
# (参考文献 http://www.din.or.jp/~ohzaki/perl.htm)
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
	|| &error("ロックディレクトリ $lfh{'dir'} が開けません。");
    @filelist = readdir(LOCKDIR);
    closedir(LOCKDIR);
    foreach (@filelist) {
	if (/^$lfh{'basename'}(\d+)/) {
	    return 1 if (time - $1 > $lfh{'timeout'} &&
		rename("$lfh{'dir'}/$_",$lfh{'current'}=$lfh{'path'}.time));
	    last;
	}
    }
    0; # ロック失敗
}

#
# アンロック
#

sub my_funlock {
    local(*lfh)=@_;
    rename($lfh{'current'},$lfh{'path'});
}

#
# MakeBNDiary -- バックナンバーファイル作成関数 --
#
# 【引数】
#   $dir  : バックナンバーディレクトリ名
#   $file : バックナンバーファイル名
#   *date : 日付 <$date{$did}>
#   *title: 題名 <$title{$did}>
#   *body : 内容 <$body{$did}>
#   *dids : 追加/削除する日記のDiaryID <@dids>
# 【事前に準備しておくグローバル変数】
#   $TMPBNFILE: バックナンバー用テンプレートファイル
#   $SIGNATURE: 署名
#   $CFG{'prev_month'}: 先月へのリンク先(デフォルト)
#   $CFG{'next_month'}: 来月へのリンク先(デフォルト)
# 【追加するとき】
#   $date{$did}、$title{$did}、$body{$did}を用意してから
#   &MakeDiary($dir,$file,*date,*title,*body,*dids)を実行
# 【削除するとき】
#   &MakeDiary($dir,$file,'','','',*dids)を実行
# 【動作】
#   (1)バックナンバー用テンプレートファイルを読む
#   (2)ファイルロック
#   (3)バックナンバーファイルを読む
#   (4)変数上で日記を追加/削除する
#   (5)バックナンバーファイルを作成する
#   (6)ファイルロック解除
#   (7)必要ならば先月および来月のファイルを空更新する
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
    # (1)バックナンバー用テンプレートファイルを読む
    #

    # 読み込み
    open(FH,$CFG{'diary_tmp_file'})
	|| &error("日記テンプレートファイル $CFG{'diary_tmp_file'} が開けません。");
    $filecont=join("",<FH>);
    close(FH);

    # 解析&エラーチェック
    &AnalyzeTmpbn(*filecont,*tmpbnhead,*opt,*tmpbnbody,*tmpbnfoot)
	|| &ErrorTmpbn;
    $tmpbnrev=1 if ($opt=~/reverse/);

    #
    # (2)ファイルロック
    #

    &my_flock(*lfh) || &error("ファイルロックに失敗しました。");

    #
    # (3)バックナンバーファイルを読む
    #

    if (open(FH,"$dir/$file")){ # openできなくてもエラーメッセージは不要
	$filecont=join("",<FH>);
	# 日記部を切り出し、DID、DATE、TITLE、BODY抽出
	&Contents2DTB($filecont,*bndate,*bntitle,*bnbody);
	close(FH);
    }

    #
    # (4)変数上でバックナンバーを作成
    #

    # 先月/来月へのリンク
    if ($tmpbnhead=~/<!--\s*akiary_prevmonth\s*-->/i ||
	$tmpbnfoot=~/<!--\s*akiary_prevmonth\s*-->/i ){
	$akiary_prevmonth=1; # 先月へのリンクあり
    }
    if ($tmpbnhead=~/<!--\s*akiary_nextmonth\s*-->/i ||
	$tmpbnfoot=~/<!--\s*akiary_nextmonth\s*-->/i ){
	$akiary_nextmonth=1; # 来月へのリンクあり
    }
    # 先月/来月へのリンクあり
    if ($akiary_prevmonth==1 || $akiary_nextmonth==1){
	# 前回と次回のファイルを探す
	($prevmonth,$nextmonth)=&GetPNFile($dir,$file);
	# 先月へのリンク作成
	if ($prevmonth ne ""){
	    $tmpbnhead=~s/<!--\s*akiary_prevmonth\s*-->/<a href="$prevmonth">/ig;
	    $tmpbnhead=~s/<!--\s*\/akiary_prevmonth\s*-->/<\/a>/ig;
	    $tmpbnfoot=~s/<!--\s*akiary_prevmonth\s*-->/<a href="$prevmonth">/ig;
	    $tmpbnfoot=~s/<!--\s*\/akiary_prevmonth\s*-->/<\/a>/ig;
	}
	# 来月へのリンク作成
	if ($nextmonth ne ""){
	    $tmpbnhead=~s/<!--\s*akiary_nextmonth\s*-->/<a href="$nextmonth">/ig;
	    $tmpbnhead=~s/<!--\s*\/akiary_nextmonth\s*-->/<\/a>/ig;
	    $tmpbnfoot=~s/<!--\s*akiary_nextmonth\s*-->/<a href="$nextmonth">/ig;
	    $tmpbnfoot=~s/<!--\s*\/akiary_nextmonth\s*-->/<\/a>/ig;
	}
    }

    # 署名挿入
    $tmpbnfoot=~s/<\/body>/$SIGNATURE<\/body>/ig;

    # 日記追加or削除
    foreach(@dids){
	if ( defined($date{$_}) ){ # 事前に準備されていたら追加
	    $bndate{$_} =$date{$_};
	    $bntitle{$_}=$title{$_};
	    $bnbody{$_} =$body{$_};
	} else { # 事前に準備されてなければ削除
	    delete $bndate{$_};
	}
    }

    #
    # (5)日記ファイルを作成する
    #

    # 作成前にファイルがあったか
    $existbefore=1 if (-e "$dir/$file");

    # ファイル削除or作成
    if (scalar(keys %bndate) > 0){ # 日記があれば作成
	open(FH,">$dir/$file")
	    || &error("日記ファイル $dir/$file に書き込めません。");

	# head部作成
	print FH $tmpbnhead;

	# 日付でソート
	@k=&SortedDID(*bndate);
	@k=reverse(@k) if ($tmpbnrev==1);

	# body部作成
	foreach(@k){
	    print FH qq(<a name="$bndate{$_}"></a><a name="$_"></a>);
	    print FH "<!--akiary_diary did=$_ date=$bndate{$_}-->";
	    $tmp=$tmpbnbody;
	    # 日付
	    $dates=&date2sdate($bndate{$_});
	    $w3cdtf=&date2sdate($bndate{$_}, '%Y0-%M1-%D1', 1);
	    $tmp=~s/<!--\s*akiary_date\s*-->/$dates/g;
	    $tmp=~s/<!--\s*akiary_w3cdtf\s*-->/$w3cdtf/g;
	    # タイトル
	    $tmp=~s/<!--\s*akiary_title\s*-->/<!--akiary_title-->$bntitle{$_}<!--\/akiary_title-->/;
	    $tmp=~s/<!--\s*akiary_title_2\s*-->/$bntitle{$_}/g;
	    # 日記本文
	    $tmp=~s/<!--\s*akiary_body\s*-->/<!--akiary_body-->$bnbody{$_}<!--\/akiary_body-->/;
	    # 生did
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

	# foot部作成
	print FH $tmpbnfoot;

	close(FH);
    } else { # 日記がない場合
	unlink("$dir/$file");
    }

    # 作成後にファイルができたか
    $existafter=1 if (-e "$dir/$file");

    #
    # (6)ファイルロック解除
    #

    &my_funlock(*lfh); # ロック解除

    #
    # (7)必要ならば先月および来月のファイルを空更新する
    #

    if ($existbefore!=$existafter){ # 新規作成もしくは削除されたとき
	# 先月へのリンクがあって来月のファイルがあれば
	if ($akiary_prevmonth==1 && $nextmonth ne $CFG{'next_month'}){
	    &MakeBNDiary($dir,$nextmonth,'','','','');
	}
	# 先月へのリンクがあって来月のファイルがあれば
	if ($akiary_nextmonth==1 && $prevmonth ne $CFG{'prev_month'}){
	    &MakeBNDiary($dir,$prevmonth,'','','','');
	}
    }
}

#
# 前回と次回のファイルを探す
#
sub GetPNFile{
    local($dir,$file)=@_;
    local(@files);
    local($prev,$next);

    opendir(DIR,$dir) || &error("日記ディレクトリ「$dir」が開けません。");
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
# 日付とDID(Diary ID)で比較するソート用関数
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
# オプショナル日記ファイル作成
# 【引数】
#   $tmpfile: オプショナル日記テンプレートファイル
#   $outfile: オプショナル日記ファイル
# 【動作】
#   1. テンプレートファイルを変数に読み込む
#   2. 変数中の<!-- akiary_\w+ -->タグを適切に置換する
#   3. 変数を出力ファイルに書き込む
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
    # 1. テンプレートファイルを変数に読み込む
    #
    open(FH,$tmpfile)
	|| &error("オプショナル日記のテンプレートファイル $tmpfile が開けません。");
    $file=join("",<FH>);
    close(FH);

    #
    # 2. 変数中の<!-- akiary_.+ -->タグを適切に置換する
    #

    # <!-- akiary_diary -->から<!-- /akiary_diary -->を置換
    if ($file=~/<!--\s*akiary_diary\s+[^>]*-->[\000-\377]*<!--\s*\/akiary_diary\s*-->/){
	# (1)開始タグ以前(2)開始タグから終了タグまで(3)終了タグ以降に分離
	$prematch=$`;
	$match=$&;
	$postmatch=$';

	# (2)開始タグから終了タグまでを日記に置換
	($match,$latest_times)=&AkiaryDiaryTag2Diary(*CFG,$match);

	# (1)(2)(3)を再結合
	$file=$prematch . $match . $postmatch;
    }

    # <!-- akiary_latest_times -->を置換
    $file =~ s/<!--\s*akiary_latest_times\s*-->/$latest_times/g;

    # <!-- akiary_lastmonth -->
    # <!-- akiary_thismonth -->
    # <!-- akiary_index --> の置換の準備
    opendir(DIR,$CFG{'diary_dir'})
	    || &error("日記ディレクトリ「$CFG{'diary_dir'}」が開けません。");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    # オプショナル日記ファイルから日記ファイルへの相対パスを求める
    local($rp,$optdir);
    ($optdir=$outfile)=~s|[^/]*$||;
    $rp=&RelativePath($optdir,$CFG{'diary_dir'});
    unless(defined($rp)){
	&error("オプショナル日記ファイル「$outfile」から日記ディレクトリ「$CFG{'diary_dir'}」への相対パスが求められません。");
    }
    $rp.='/' if ($rp ne '');

    # <!-- akiary_lastmonth -->と<!-- /akiary_lastmonth -->を置換
    $lastmonth=$files[$#files];
    if ($lastmonth ne ""){
	$file =~ s/<!--\s*akiary_lastmonth\s*-->/<a href="$rp$lastmonth">/ig;
	$file =~ s/<!--\s*\/akiary_lastmonth\s*-->/<\/a>/ig;
    }

    # <!-- akiary_thismonth -->から<!-- /akiary_thismonth -->を置換
    ($y,$m)=&get_todays_date;
    $thismonth=sprintf("%04d%02d.html",$y,$m);
    ($thismonth)=grep(/^$thismonth$/,@files);
    if ($thismonth ne ""){
	$file =~ s/<!--\s*akiary_thismonth\s*-->/<a href="$rp$thismonth">/ig;
	$file =~ s/<!--\s*\/akiary_thismonth\s*-->/<\/a>/ig;
    }

    # <!-- akiary_index -->を置換
    if ($file =~ /<!--\s*akiary_index\s*-->/i){
	# 文字列変換の準備
	@m2=('Jan','Feb','Mar','Apr','May','Jun',
	     'Jul','Aug','Sep','Oct','Nov','Dec');
	@m3=('January','February','March','April','May','June',
	     'July','August','September','October','November','December');
	# 各月へのリンクを作ったり間を埋めたり
	@files = reverse @files if ($CFG{'index_format_rev_month'} == 1);
	foreach (@files){
	    ($y,$m) = (/^(\d{4})(\d{2})/);
	    $tmp = $CFG{'index_format_month'};
	    $tmp =~ s/%Y0/$y/g;                      # 4桁西暦
	    $tmp =~ s/%Y1/sprintf("%02d",$y%100)/eg; # 2桁西暦
	    $tmp =~ s/%Y2/$y-1988/eg;                # 元号
	    $tmp =~ s/%M0/sprintf("%d",$m)/eg;   # 月
	    $tmp =~ s/%M1/sprintf("%02d",$m)/eg; # 月(0付き)
	    $tmp =~ s/%M2/$m2[$m-1]/g;          # 月(英語短縮)
	    $tmp =~ s/%M3/$m3[$m-1]/g;          # 月(英語)
	    if (defined($index{$y})){
		$index{$y} .= $CFG{'index_format_between_months'};
	    }
	    $index{$y} .= "<a href=\"$rp$_\">$tmp</a>";
	}

	# 各年を入れたり
	$index = '';
	@y = sort keys %index;
	@y = reverse @y if ($CFG{'index_format_rev_year'} == 1);
	foreach $y (@y){
	    $tmp = $CFG{'index_format_begin'};
	    $tmp =~ s/%Y0/$y/g;                      # 4桁西暦
	    $tmp =~ s/%Y1/sprintf("%02d",$y%100)/eg; # 2桁西暦
	    $tmp =~ s/%Y2/$y-1988/eg;                # 元号
	    $index .= $tmp . $index{$y} . $CFG{'index_format_end'};
	}

	# 置換
	$file =~ s/<!--\s*akiary_index\s*-->/$index/ig;
    }

    # </body>の直前に$SIGNATUREを挿入
    $file =~ s/<\/body>/$SIGNATURE\n<\/body>/ig; # 署名挿入

    #
    # 3. 変数を出力ファイルに書き込む
    #
    open(FH,">$outfile")
	|| &error("オプショナル日記ファイル $outfile に書き込めません。");
    print FH $file;
    close(FH);
}

#
# <!-- akiary_diary [^>]*-->から<!-- /akiary_diary -->を日記に置換
#

sub AkiaryDiaryTag2Diary{
    local(*CFG,$match)=@_;
    local($option,$reverse,$latest_times);
    local(@files,$file,$contents);
    local(%date,%title,%body);
    local(@k,$ret,$tmp);

    #
    # (1)akiary_diaryタグ解析
    #
    $match =~ /<!--\s*akiary_diary\s+([^>]*)\s*-->([\000-\377]*)<!--\s*\/akiary_diary\s*-->/;
    $option = $1;
    $match = $2;  # 開始タグと終了タグを除去

    # reverse or not
    $reverse = 1 if ($option =~ /reverse/i);

    # latest_times
    $latest_times = $CFG{'latest_times'};
    if ($option =~ /latest_times\s*=\s*"(\d+)"/){
	$latest_times = $1;
    }

    #
    # (2)日記ファイルを読む
    #
    opendir(DIR,$CFG{'diary_dir'})
	|| &error("日記ディレクトリ「$CFG{'diary_dir'}」が開けません。");
    @files=sort(grep(/^\d{6}(\d{2})?\.html$/,readdir(DIR)));
    closedir(DIR);

    foreach $file (reverse @files){
	open(FH,"$CFG{'diary_dir'}/$file")
	    || &error("日記ファイル「$CFG{'diary_dir'}/$file」が開けません。");
	$contents = join("",<FH>);
	close(FH);
	# 日記部を切り出し、DID、DATE、TITLE、BODY抽出
	&Contents2DTB($contents,*date,*title,*body);
	last if (scalar(keys %date) >= $latest_times);
    }

    #
    # (3)最新版日記を変数上で作成
    #

    @k=&SortedDID(*date);
    $latest_times = $#k + 1 if ($latest_times > $#k);
    @k=splice(@k,-$latest_times,$latest_times);
    @k=reverse(@k) if ($reverse==1);
    foreach(@k){
	$ret .= qq(<a name="$date{$_}"></a><a name="$_"></a>);
	$tmp=$match;
	# 日付
	$dates=&date2sdate($date{$_});
	$w3cdtf=&date2sdate($date{$_}, '%Y0-%M1-%D1', 1);
	$tmp=~s/<!--\s*akiary_date\s*-->/$dates/g;
	$tmp=~s/<!--\s*akiary_w3cdtf\s*-->/$w3cdtf/g;
	# タイトル
	$tmp=~s/<!--\s*akiary_title\s*-->/$title{$_}/;
	$tmp=~s/<!--\s*akiary_title_2\s*-->/$title{$_}/g;
	# 日記本文
	$tmp=~s/<!--\s*akiary_body\s*-->/$body{$_}/;
	# 生did
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
#   ディレクトリパス$fromdirからディレクトリパス$todirへの相対パスを返す
#   (例)&RelativePath("a/b/c" ,"a/b/d" ) -> "../d"
#       &RelativePath("a/b/c" ,"d/e/f" ) -> "../../../d/e/f"
#       &RelativePath("a/b/c" ,"a"     ) -> "../.."
#       &RelativePath("/a/b/c","/a/b/d") -> "../d"
#       &RelativePath("/a/b/c","a/b/d" ) -> undef
#
sub RelativePath {
    # 絶対パスと相対パスとの相対パスは求められない
    if ( ($_[0] =~ m|^/| && $_[1] !~ m|^/|) ||
	 ($_[0] !~ m|^/| && $_[1] =~ m|^/|) ){
	return;
    }
    # 引数を各ディレクトリに分解(「//」「./」は除去)
    local(@fromdirs)=grep(!/^\.?$/,split('/',$_[0]));
    local(@todirs)  =grep(!/^\.?$/,split('/',$_[1]));
    # 共通パスを除去
    while($fromdirs[0] eq $todirs[0]){
	last unless shift(@fromdirs);
	last unless shift(@todirs);
    }
    # $fromdirから親ディレクトリに移動
    while(shift(@fromdirs)){
	unshift(@todirs,'..');
    }
    # 相対パスを返す
    join('/',@todirs);
}

#
# 「&<>"」をエスケープする
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
# 日付から日記ファイル名に変換
#
# 【設定】$CFG{'dfile_div_mday'}: 日記ファイルを分割する日
# 【引数】$date: yyyymmdd形式の日付
# 【返値】$dfn: yyyymm.htmlおよびyyyymmdd.html形式の日記ファイル名
#
# 例)$CFG{'dfile_div_mday'} eq ''
#      &date2dfn('20020327') -> '200203.html'
#    $CFG{'dfile_div_mday'} eq '1 16'
#      &date2dfn('20020327') -> '20020316.html'
#    $CFG{'dfile_div_mday'} eq '1 11 21'
#      &date2dfn('20020327') -> '20020321.html'
#
sub date2dfn{
    local($date)=@_;
    local(@div_date);

    # 引数がおかしいときはそのままreturn
    (local($y,$m,$d)=($date=~/(\d{4})(\d{2})(\d{2})/)) || return;

    # $CFG{'dfile_div_mday'}に指定がないときはyyyymm.html形式を返す
    (@div_date=split(' ',$CFG{'dfile_div_mday'})) || return("$y$m.html");

    # $CFG{'dfile_div_mday'}に指定があるとき
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
