#! /usr/local/bin/perl -w

use strict;
use vars qw($conf $VERSION);
use Fcntl qw(:flock);
# use CGI::Carp qw(fatalsToBrowser);
# use Jcode;

# package aki2rss;
# version: 0.92 2004-04-11
$VERSION = '0.92';

=pod

=head1 名前

aki2rss.cgi - Akiaryオプショナル日記からRSSを生成する。

=head1 概要

INPUT
	query	特になし
	file	特別な形式のAkiaryオプショナル日記
OUTPUT
	stdout	html
	file	RSS 1.0

=head1 説明

◆RSS仕様
RSS1.0準拠
EUC-JP、SHIFT_JIS、UTF-8に対応。
（文字コードは、日記、RSS、設定ファイル、CGIスクリプト…すべてで同じにします。）

◆特徴
カテゴリは設定しません。
<textinput>要素には対応しません。
Dublin Coreモジュールによる拡張（一部機能）を装備。
<dc:date>要素を設定します。
要約は、単に頭から何文字という形で切り出します。

◆前提となるオプショナル日記の形式
↓↓ここから↓↓
##entry##<!-- akiary_diary reverse latest_times="10" -->
##date##<!--akiary_date-->
##title##<!--akiary_title-->
##body##<!--akiary_body-->

##entry##<!--/akiary_diary-->
↑↑ここまで↑↑

行頭から始まる「##entry##, ##date##, ##title##, ##body##」がカラムの区切りになっています。
##entry##のみは行頭でなくても区切りとして機能しますが、通常は行頭にしてください。
順序は固定で、区切りは各1コずつ必要です。「##entry##」以外は中身が空でもとりあえず処理できます。
「##entry##」がレコードの区切り（始まりの印）になっています。ファイルの末尾は「##entry##」で終わります。
日記本文も含めて、各カラムには上記の区切り文字列を含まないこと。エスケープ処理は規定していません。
latest_timesでitemの数を指定します。値の範囲は1～15を推奨します。

◆将来の計画
Shift_JISとUTF-8における要約切り出しは手抜きです。文の途中でも構わずぶった切るのがイマイチ。
設定を別ファイルから読み込むようにする。それによって文字コード絡みの問題はほぼ解決できるはずだ。

◆改変履歴
2004-04-11 改行問題を解消。1レコード1行の縛りがなくなりました。
2004-02-18 Latin-1文字実体参照のDTDを削除。<trackback:ping>要素に実験的に対応（未公開）。
2003-11-04 version 0.90 プレビューリリース
リリース前
2003-11-02 Shift_JISとUTF-8対応の要約の切り出しを実装。日付の取得方法を改良。
2003-09-23 XSLT対応。
2003-09-16 image要素対応。要約の切り出しを実装。EUC-JPのみという大きな縛りはあるものの、だいぶ良くなってきている。
2003-08-19 仕様のバグを発見。
2003-08-06 自サイト専用につくる。RSS1.0。

=head1 参考資料

以下のサイトからPerlのコードを参考・利用させていただきました。
http://www.din.or.jp/~ohzaki/perl.htm
http://nais.to/~yto/tools/jbuncut/
http://niaou.alib.jp/diary/diary-10-2003C.html#diary-10-21-2003-A
http://hasunuma.pobox.ne.jp/support/cyclamen.cgi?log=perl&tree=r20

=head1 作者

auther:  いしだなおと
mailto:  not2000@anet.ne.jp
website: http://isnot.jp/?p=Akiary

=head1 ライセンス(=LICENSE)

「Artistic License」という、Perlが採用しているライセンスに準じます。
参考日本語訳：
http://www.opensource.jp/artistic/ja/Artistic-ja.html

This program is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut

###############################
# 設定はここから
###############################

$conf = {
# 日記を置くディレクトリをあらわすURL。「/」でおわること。
'uri_base'      => 'http://www.ikkyotf.jp/contents/notice/',
# 日記ディレクトリ。サーバーでの（ファイルシステムの）パス。「/」でおわること。
'diary_dir'     => '../contents/notice/',
# xml lang
'lang'          => 'ja',
# xml encoding 右のいずれか。[ shift_jis | euc-jp | utf-8 ] ※日記htmlのエンコーディングと一致するように。
'encoding'      => 'shift_jis',
# 要約の分量を文字数で指定します。EUC-JPの場合は74、Shift_JISかUTF-8なら250程度。
'desc_limit'    => '250',
# 要約の最大限の長さ。変更しないように。
'desc_limit_hard'    => '252',
# TimeZone。サーバーの時計がJSTなら'+09:00'で、UTCなら'+00:00'もしくは'Z'
'tz'            => '+09:00',

# filename => {},
# channel => {dc => {}},
# image => {},
# separator => {},
};

$conf->{channel} = {
# サイトのURL（もしくは最新の日記のURL）
'link'          => 'http://www.ikkyotf.jp/contents/notice/new.html',
# サイトのタイトル
'title'         => '一橋大学陸上部OBOG連絡',
# サイトの説明
'description'   => 'OBOGの先輩向けのお知らせです',
};

$conf->{channel}->{dc} = {
# 作者
'creator'       => '一橋大学陸上競技部',
# 著作権表示
'rights'        => 'copy right (c)Hitotsubashi Univ. Track&#38;Field Club',
'language'      => "$conf->{lang}",
'title'         => "$conf->{channel}->{title}",
# 'publisher'     => "$conf->{channel}->{title}",
};

$conf->{image} = {
# サイトの画像（ロゴ、アイコン）
# <image>要素は省略することができます。そのときはurlを空文字列にします。
# 'url'           => '',
'url'           => '',
'title'         => "$conf->{channel}->{title}",
'link'          => "$conf->{channel}->{link}",
};

$conf->{langset} = {
'nikki'         => '日記',
};

$conf->{separator} = {
# Akiaryオプショナル日記からデータを切り出す時の目印。
'entry'         => '##entry##',
'date'          => '##date##',
'title'         => '##title##',
'body'          => '##body##',
};

$conf->{filename} = {
# Akiaryオプショナル日記。形式は別記の説明を参照。
'recent_info'   => 'new.txt',
# 生成されるRSSのファイル名
'rss'           => 'index.rdf',
# XSLT（不要なら指定しなくてもよい）
#'xslt'          => 'rss10general.xsl',
};


###############################
# 設定はここまで
###############################


&output_rss10(&analyze_recent_info());

&fin(
	scalar localtime(time()) . 
	qq{<br />
		Generate RSS.<br />
	}
);
exit;



sub analyze_recent_info {
	# 最新情報解析 ソースからタイトル、リンク、説明文などを抽出

	my $file = $conf->{filename}->{recent_info}; # ファイル名
	$file =~ s/[\<\>\|\`]//; # よくない記号を除去
	$file =~ s/.*[\\\/]//; # パスを除去

	# 入力ファイルを一気に読みこむ
	my $recent = '';
	{
		local $/;
		open(RECENT, "< $conf->{diary_dir}$file") || &error('can not open file.' . $!);
		$recent = <RECENT>;
		close(RECENT);
	}

	# 記事ごとに分解
	my @entries = split /\Q$conf->{'separator'}->{'entry'}\E/, $recent;

	# regex
	my $re = q{^\s*(.*?)\s*\n} 
		. $conf->{'separator'}->{'date'} 
		. q{\s*(.*?)\s*\n} 
		. $conf->{'separator'}->{'title'} 
		. q{\s*(.*?)\s*\n} 
		. $conf->{'separator'}->{'body'} 
		. q{\s*(.*?)\s*\n$};

	# 記事ごとの処理
	my @items = ();
	foreach my $entry (@entries) {
		next unless $entry;
		$entry =~ /$re/os;
		my($anchor, $chunk, $title, $body) = ($1, $2, $3, $4);
		my($link, $dcdate, $akidate, $tb_uri) = &proc_anchor(\$anchor, \$chunk);
		my $description = &trim($body);
		$title = &delete_tag($title) || $akidate || '';
		#&trim_space(\$title);

		&escape_xml(\$link, \$title, \$description, \$tb_uri);
		push(@items, {
			'link'        => "$link", 
			'title'       => "$title", 
			'description' => "$description", 
			'content'     => {'encoded' => "$body"}, 
			'dc'          => {'date'    => "$dcdate"}, 
			'trackback'   => {'ping'    => "$tb_uri"}, 
		});
		# content:encodedはサニタイズしてない。ソースを信頼？？
	}
	return \@items;
}


sub rdf_head {
	my $dcdatenow = &time2dcdate(time());
	my $xslt = $conf->{filename}->{xslt} eq '' ? 
		'' : qq(<?xml-stylesheet href="$conf->{filename}->{xslt}" type="text/xsl" media="screen" ?>);

	return qq{<?xml version="1.0" encoding="$conf->{encoding}" ?>
$xslt
<rdf:RDF
 xmlns="http://purl.org/rss/1.0/"
 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" 
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:content="http://purl.org/rss/1.0/modules/content/"
 xmlns:trackback="http://madskills.com/public/xml/rss/module/trackback/"
 xml:lang="$conf->{lang}"
>
 <channel rdf:about="$conf->{uri_base}$conf->{filename}->{rss}">
  <title>$conf->{channel}->{title}</title>
  <link>$conf->{channel}->{link}</link>
  <description>$conf->{channel}->{description}</description>
  <dc:language>$conf->{channel}->{dc}->{language}</dc:language>
  <dc:title>$conf->{channel}->{dc}->{title}</dc:title>
  <dc:creator>$conf->{channel}->{dc}->{creator}</dc:creator>
  <dc:rights>$conf->{channel}->{dc}->{rights}</dc:rights>
  <dc:date>$dcdatenow</dc:date>
  <items>
   <rdf:Seq>
}; #end qq
}

sub rdf_mid {
	my $res = qq{   </rdf:Seq>
  </items>
}; #end qq

# if exists '$conf->{image}->{url}'
	$res .= qq{  <image rdf:resource="$conf->{image}->{url}"/>
} if ($conf->{image}->{url});

# end of channel element
	$res .= qq( </channel>\n);

# if exists '$conf->{image}->{url}'
	$res .= qq{
 <image rdf:about="$conf->{image}->{url}">
  <title>$conf->{image}->{title}</title>
  <link>$conf->{image}->{link}</link>
  <url>$conf->{image}->{url}</url>
 </image>
} if ($conf->{image}->{url});

	return $res;
}

sub rdf_foot {
	return qq(\n</rdf:RDF>\n);
}

sub output_rss10 {
	my $refitems = shift;
	my $file = $conf->{filename}->{rss}; # ファイル名
	$file =~ s/[\<\>\|\`]//; # よくない記号を除去
	$file =~ s/.*[\\\/]//; # パスを除去

	# 出力
	open(RSS, "> $conf->{diary_dir}$file.temp") || &error('can not open file.' . $!);
	flock(RSS, LOCK_EX);

	# <channel>
	print RSS &rdf_head();
	foreach (@$refitems) {
		print RSS qq(    <rdf:li rdf:resource="$conf->{uri_base}$_->{link}" />\n);
	}
	print RSS &rdf_mid();

	# <item>
	# <trackback:ping rdf:resource="$_->{trackback}->{ping}" />
	foreach (@$refitems) {
	  print RSS qq{
 <item rdf:about="$conf->{uri_base}$_->{link}">
  <title>$_->{title}</title>
  <link>$conf->{uri_base}$_->{link}</link>
  <description>
$_->{description}
  </description>
  <content:encoded><![CDATA[
$_->{content}->{encoded}
]]></content:encoded>
  <dc:publisher>$conf->{channel}->{title}</dc:publisher>
  <dc:date>$_->{dc}->{date}</dc:date>
 </item>
}; #end qq
	} #end loop
	print RSS &rdf_foot();

	close(RSS);

	# finaly, replace rss file.
	rename "$conf->{diary_dir}$conf->{filename}->{rss}.temp", "$conf->{diary_dir}$conf->{filename}->{rss}";

}


sub trim_space {
	foreach my $refs (@_) {
		$$refs =~ tr/\x0D\x0A//;
		$$refs =~ s/[\r\n]//g;
		$$refs =~ s/[\f\t\a\b]//g;
		$$refs =~ s/^\s+(.*?)\s+$/$1/;
		$$refs =~ s/\s+/ /g;
	}
}

sub escape_xml {
	foreach my $refs (@_) {
		$$refs =~ s/&quot;/"/g;
		$$refs =~ s/&apos;/'/g;
		$$refs =~ s/&lt;/</g;
		$$refs =~ s/&gt;/>/g;
		$$refs =~ s/&amp;/&/g;
		$$refs =~ s/&/&amp;/g;
		$$refs =~ s/</&lt;/g;
		$$refs =~ s/>/&gt;/g;
		$$refs =~ s/\"/&quot;/g;
		$$refs =~ s/\'/&apos;/g;
	}
}


sub time2dcdate {
	# まったくナンセンスな処理である。あえて目をツブル。
	if ($conf->{tz} eq '+09:00') {
		$ENV{'TZ'} = "JST-9";
	} else {
		$ENV{'TZ'} = '';
	}

	my($time, $date) = @_;
	my($sec, $min, $hour, $mday, $mon, $year) = (localtime($time))[0..5];
	$year += 1900;
	$mon++;

	if (defined $date) {
		$year = substr($date, 0, 4);
		$mon  = substr($date, 4, 2);
		$mday = substr($date, 6, 2);
	}

	my $dcdate = sprintf("%04d-%02d-%02dT%02d:%02d:%02d", $year, $mon, $mday, $hour, $min, $sec);
	$dcdate .= "$conf->{tz}";

	return $dcdate;
}

sub date2dcdate {
	my $date = shift;
	$date =~ s/(\d{4})(\d{2})(\d{2})/sprintf("%04d-%02d-%02d", $1, $2, $3)/e;
	return $date;
}

sub date2uri {
	my $date = shift;
	my($ym, $d) = $date =~ /(\d{6})(\d{2})/;
	return join('', ($ym, '.html#', $ym, $d));
}

sub did2uri {
	my($did, $date) = @_;
	my $ym = substr($date, 0, 4);
	return join('', ($ym, '.html#', $did));
}

sub proc_anchor {
# 条件
# a name did  [ある|ない]
# a name date [ある|ない]
# 「a name did」「a name date」少なくとも片方がある
# a href did  [ある|ない]
# a href date [ある|ない]
# 「a href did」「a href date」ともにないか、もしくはいずれか片方がある
# 属性値      [「"」で囲まれている|「'」で囲まれている|「裸の値」]

	my $refanchor = shift;
	my $refchunk = shift;
	my($date, $time, $did, $dcdate, $akidate, $uri, $tb_uri);

	# uriを探す。
	if ($$refchunk =~ m|href\s*=\s*[\"\']?(\d{6}\.html#\d{8})(_\d{9,10})[\"\']?|) {
		$uri = $1 . $2;
	}

	# dateを探す。
	$$refanchor =~ m/\D(\d{8})\D\D+/;
	$date = $1;

	# didを探す。
	$$refanchor =~ m/(id|name)\s*=\s*[\"\']?(\d{8})_(\d{9,10})[\"\']?/;
	$date = $date || $2;
	$time = $3;
	$did  = $2 . '_' . $3;

	&error('anchor is not detected.' . $!) unless defined $date;

	# uriとdcdateを決定。uriはdateから組み立てる
	if     (defined $time && defined $date) {
		$uri    = $uri || &date2uri($date);
		$dcdate = &time2dcdate($time, $date);
	} elsif (defined $date) {
		$uri    = $uri || &date2uri($date);
		$dcdate = &date2dcdate($date);
	} else {
		&error('date is not detected.');
	}

	# Akiaryにより変換された日付を探す。
	$akidate = delete_tag($$refchunk);

	# tb_uriを探す。これは汎用的ではない…当面はプロトタイプ。
	if ($$refchunk =~ m/href="(\S+?)"([^>]*?)>WikiBack\//) {
		$tb_uri = $1 || '';
	}

	return ($uri, $dcdate, $akidate, $tb_uri);
}


sub delete_tag {
	my $str = shift;

	# <br />タグを保存する
	$str =~ s/(&lt;|<)\s*[b|B][r|R].*?(&gt;|>)/\0/g;

	## via: http://www.din.or.jp/~ohzaki/perl.htm
	# HTMLタグの正規表現 $tag_regex
	my $tag_regex_ = q{[^"'<>]*(?:"[^"]*"[^"'<>]*|'[^']*'[^"'<>]*)*(?:>|(?=<)|$(?!\n))}; #'}}}}
	my $comment_tag_regex = '<!(?:--[^-]*-(?:[^-]+-)*?-(?:[^>-]*(?:-[^>-]+)*?)??)*(?:>|$(?!\n)|--.*$)';
	my $tag_regex = qq{$comment_tag_regex|<$tag_regex_};
	my $text_regex = q{[^<]*};

	# $str の中のタグを削除した $result を作る
	my $result = '';
	while ($str =~ /($text_regex)($tag_regex)?/gso) {
	  last if (defined $1 and $1 eq '' and defined $2 and $2 eq '');
	  $result .= $1;
	  my $tag_tmp = $2 || '';
	  if ($tag_tmp =~ m/^<(XMP|PLAINTEXT|SCRIPT)(?![0-9A-Za-z])/i) {
	    $str =~ /(.*?)(?:<\/$1(?![0-9A-Za-z])$tag_regex_|$)/gsi;
	    (my $text_tmp = $1) =~ s/</&lt;/g;
	    $text_tmp =~ s/>/&gt;/g;
	    $result .= $text_tmp;
	  }
	}

	$result =~ tr/\0/\n/;
	return $result;
}

sub trim {
	my $total = &delete_tag(shift);

	my $stay = '';
	if    (lc($conf->{encoding}) eq 'euc-jp') {
		$stay = &trim_euc($total);
	} elsif(lc($conf->{encoding}) eq 'shift_jis') {
		$stay = &z_substr($total, 0, $conf->{desc_limit}, 1);
	} elsif(lc($conf->{encoding}) eq 'utf-8') {
		$stay = &hoge(substr($total, 0, $conf->{desc_limit}));
	} else {
		return '';
	}

	$stay .= length($stay) < int($conf->{desc_limit}) ? '' : '...';
	return $stay;
# 	return $total;
}

sub trim_euc {
	## via: http://nais.to/~yto/tools/jbuncut/
	# 文字を一文字ずつ処理（日本語対応。漢字コードはEUCとする）
	my $result = shift;
	my($ret, $i) = ('', '0');
	while ($result =~ /([\xa1-\xfe]{2}|\x8e[\xa1-\xdf]|\x8f[\xa1-\xfe]{2}|.)/g) {
		$ret .= $1;
		if ($1 =~ /(。|．)/) {
			$ret .= "\n";
			last if $i++ > int($conf->{desc_limit});
		}
		last if $i++ > int($conf->{desc_limit_hard});
	}
	return $ret
}


## via: http://niaou.alib.jp/diary/diary-10-2003C.html#diary-10-21-2003-A
# (c) 1999-2003 NiAOU All Rights Reserved.
# $_ の中身が utf-8 であることが前提。
# our $str = substr($_, 0, 255);
# print hoge($str);
sub hoge($) {
    my $str = shift;
    my $length = length($str);
    my $drop = 0;
    if(substr($str, $length - 1, 1) =~ /^[\x80-\xBF]$/){
        if(substr($str, $length - 2, 1) =~ /^[\x80-\xBF]$/){
            if(substr($str, $length - 3, 1) =~ /^[\x80-\xBF]$/){
                if(substr($str, $length - 4, 1) =~ /^[\x80-\xBF]$/){
                    if(substr($str, $length - 5, 1) =~ /^[\xFC-\xFD]$/){
                        $drop = 5;
                    }
                }
                if(substr($str, $length - 4, 1) =~ /^[\xF8-\xFD]$/){
                    $drop = 4;
                }
            }
            if(substr($str, $length - 3, 1) =~ /^[\xF0-\xFD]$/){
                $drop = 3;
            }
        }
        if(substr($str, $length - 2, 1) =~ /^[\xE0-\xFD]$/){
            $drop = 2;
        }
    }
    if(substr($str, $length - 1, 1) =~ /^[\xC0-\xFD]$/){
        $drop = 1;
    }
    $str = substr($str, 0, $length - $drop) if $drop;
    return($str);
}
# hint: uft-8 の一文字の正規表現
#   [\x00-\x7F]|
#   [\xC0-\xDF][\x80-\xBF]|
#   [\xE0-\xEF][\x80-\xBF][\x80-\xBF]|
#   [\xF0-\xF7][\x80-\xBF][\x80-\xBF][\x80-\xBF]|
#   [\xF8-\xFB][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF]|
#   [\xFC-\xFD][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF]


## via: http://hasunuma.pobox.ne.jp/support/cyclamen.cgi?log=perl&tree=r20
# Shift_JIS全角文字対応の substr 関数
# 引数：文字列、開始位置、文字長、オプション（開始位置、文字長のいずれかを省略可）
# 全角文字は2文字として数えます。
# 第4引数を2とした場合には、全角文字を1文字として数えるようにしました。
# 第4引数に1を与えた場合には、切り出した結果の文字列の先頭が2バイト文字の2バイト目にあたる場合と終端が2バイト文字の1バイト目にあたる場合には、それぞれを半角スペースに置き換えて返される文字長の辻褄合わせを行うようにしました。
# ex.) z_substr("$line", 0, 100, 1);
sub z_substr {
	my($s,$p,$l,$o) = @_;
	$s =~ s/(.)/$1\0/g;
	$s =~ s/([\x81-\x9f\xe0-\xfc])\0(.)\0/$o==2?"$1$2":"$1$2\0\0"/eg;
	$s = $l eq '' ? substr($s,$p*2):substr($s,$p*2,$l*2);
	if ($o==1) { $s =~ s/^\0\0/ /; $s =~ s/.[^\0]$/ /;}
	$s =~ tr/\0//d;
	$s;
}

sub error {
    print "Content-Type: text/html; charset=$conf->{encoding}\n\n";
    print "<html><head><title>akiary2rss</title></head><body><div>$_[0]</div></body></html>";
    exit;
}

sub fin {
    print "Content-Type: text/html; charset=$conf->{encoding}\n\n";
    print <<"HTML";
<html>
<head>
<title>aki2rss.cgi</title>
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Cache-Control" content="no-cache">
<meta http-equiv="ROBOT" content="NOINDEX,NOFOLLOW">
<meta http-equiv="refresh" content="3;url=$conf->{channel}->{link}">
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
[<a href="$conf->{channel}->{link}" target="diary">$conf->{langset}->{nikki}</a>]
<div class="title">aki2rss.cgi</div>
<div class="subtitle">$_[0]</div>
<hr>
</body>
</html>
HTML
    exit;
}

1;
