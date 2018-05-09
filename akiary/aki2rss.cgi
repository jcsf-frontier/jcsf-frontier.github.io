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

=head1 ���O

aki2rss.cgi - Akiary�I�v�V���i�����L����RSS�𐶐�����B

=head1 �T�v

INPUT
	query	���ɂȂ�
	file	���ʂȌ`����Akiary�I�v�V���i�����L
OUTPUT
	stdout	html
	file	RSS 1.0

=head1 ����

��RSS�d�l
RSS1.0����
EUC-JP�ASHIFT_JIS�AUTF-8�ɑΉ��B
�i�����R�[�h�́A���L�ARSS�A�ݒ�t�@�C���ACGI�X�N���v�g�c���ׂĂœ����ɂ��܂��B�j

������
�J�e�S���͐ݒ肵�܂���B
<textinput>�v�f�ɂ͑Ή����܂���B
Dublin Core���W���[���ɂ��g���i�ꕔ�@�\�j�𑕔��B
<dc:date>�v�f��ݒ肵�܂��B
�v��́A�P�ɓ����牽�����Ƃ����`�Ő؂�o���܂��B

���O��ƂȂ�I�v�V���i�����L�̌`��
�����������火��
##entry##<!-- akiary_diary reverse latest_times="10" -->
##date##<!--akiary_date-->
##title##<!--akiary_title-->
##body##<!--akiary_body-->

##entry##<!--/akiary_diary-->
���������܂Ł���

�s������n�܂�u##entry##, ##date##, ##title##, ##body##�v���J�����̋�؂�ɂȂ��Ă��܂��B
##entry##�݂͍̂s���łȂ��Ă���؂�Ƃ��ċ@�\���܂����A�ʏ�͍s���ɂ��Ă��������B
�����͌Œ�ŁA��؂�͊e1�R���K�v�ł��B�u##entry##�v�ȊO�͒��g����ł��Ƃ肠���������ł��܂��B
�u##entry##�v�����R�[�h�̋�؂�i�n�܂�̈�j�ɂȂ��Ă��܂��B�t�@�C���̖����́u##entry##�v�ŏI���܂��B
���L�{�����܂߂āA�e�J�����ɂ͏�L�̋�؂蕶������܂܂Ȃ����ƁB�G�X�P�[�v�����͋K�肵�Ă��܂���B
latest_times��item�̐����w�肵�܂��B�l�͈̔͂�1�`15�𐄏����܂��B

�������̌v��
Shift_JIS��UTF-8�ɂ�����v��؂�o���͎蔲���ł��B���̓r���ł��\�킸�Ԃ����؂�̂��C�}�C�`�B
�ݒ��ʃt�@�C������ǂݍ��ނ悤�ɂ���B����ɂ���ĕ����R�[�h���݂̖��͂قډ����ł���͂����B

�����ϗ���
2004-04-11 ���s���������B1���R�[�h1�s�̔��肪�Ȃ��Ȃ�܂����B
2004-02-18 Latin-1�������̎Q�Ƃ�DTD���폜�B<trackback:ping>�v�f�Ɏ����I�ɑΉ��i�����J�j�B
2003-11-04 version 0.90 �v���r���[�����[�X
�����[�X�O
2003-11-02 Shift_JIS��UTF-8�Ή��̗v��̐؂�o���������B���t�̎擾���@�����ǁB
2003-09-23 XSLT�Ή��B
2003-09-16 image�v�f�Ή��B�v��̐؂�o���������BEUC-JP�݂̂Ƃ����傫�Ȕ���͂�����̂́A�����ԗǂ��Ȃ��Ă��Ă���B
2003-08-19 �d�l�̃o�O�𔭌��B
2003-08-06 ���T�C�g��p�ɂ���BRSS1.0�B

=head1 �Q�l����

�ȉ��̃T�C�g����Perl�̃R�[�h���Q�l�E���p�����Ă��������܂����B
http://www.din.or.jp/~ohzaki/perl.htm
http://nais.to/~yto/tools/jbuncut/
http://niaou.alib.jp/diary/diary-10-2003C.html#diary-10-21-2003-A
http://hasunuma.pobox.ne.jp/support/cyclamen.cgi?log=perl&tree=r20

=head1 ���

auther:  �������Ȃ���
mailto:  not2000@anet.ne.jp
website: http://isnot.jp/?p=Akiary

=head1 ���C�Z���X(=LICENSE)

�uArtistic License�v�Ƃ����APerl���̗p���Ă��郉�C�Z���X�ɏ����܂��B
�Q�l���{���F
http://www.opensource.jp/artistic/ja/Artistic-ja.html

This program is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut

###############################
# �ݒ�͂�������
###############################

$conf = {
# ���L��u���f�B���N�g��������킷URL�B�u/�v�ł���邱�ƁB
'uri_base'      => 'http://www.ikkyotf.jp/contents/notice/',
# ���L�f�B���N�g���B�T�[�o�[�ł́i�t�@�C���V�X�e���́j�p�X�B�u/�v�ł���邱�ƁB
'diary_dir'     => '../contents/notice/',
# xml lang
'lang'          => 'ja',
# xml encoding �E�̂����ꂩ�B[ shift_jis | euc-jp | utf-8 ] �����Lhtml�̃G���R�[�f�B���O�ƈ�v����悤�ɁB
'encoding'      => 'shift_jis',
# �v��̕��ʂ𕶎����Ŏw�肵�܂��BEUC-JP�̏ꍇ��74�AShift_JIS��UTF-8�Ȃ�250���x�B
'desc_limit'    => '250',
# �v��̍ő���̒����B�ύX���Ȃ��悤�ɁB
'desc_limit_hard'    => '252',
# TimeZone�B�T�[�o�[�̎��v��JST�Ȃ�'+09:00'�ŁAUTC�Ȃ�'+00:00'��������'Z'
'tz'            => '+09:00',

# filename => {},
# channel => {dc => {}},
# image => {},
# separator => {},
};

$conf->{channel} = {
# �T�C�g��URL�i�������͍ŐV�̓��L��URL�j
'link'          => 'http://www.ikkyotf.jp/contents/notice/new.html',
# �T�C�g�̃^�C�g��
'title'         => '�ꋴ��w���㕔OBOG�A��',
# �T�C�g�̐���
'description'   => 'OBOG�̐�y�����̂��m�点�ł�',
};

$conf->{channel}->{dc} = {
# ���
'creator'       => '�ꋴ��w���㋣�Z��',
# ���쌠�\��
'rights'        => 'copy right (c)Hitotsubashi Univ. Track&#38;Field Club',
'language'      => "$conf->{lang}",
'title'         => "$conf->{channel}->{title}",
# 'publisher'     => "$conf->{channel}->{title}",
};

$conf->{image} = {
# �T�C�g�̉摜�i���S�A�A�C�R���j
# <image>�v�f�͏ȗ����邱�Ƃ��ł��܂��B���̂Ƃ���url���󕶎���ɂ��܂��B
# 'url'           => '',
'url'           => '',
'title'         => "$conf->{channel}->{title}",
'link'          => "$conf->{channel}->{link}",
};

$conf->{langset} = {
'nikki'         => '���L',
};

$conf->{separator} = {
# Akiary�I�v�V���i�����L����f�[�^��؂�o�����̖ڈ�B
'entry'         => '##entry##',
'date'          => '##date##',
'title'         => '##title##',
'body'          => '##body##',
};

$conf->{filename} = {
# Akiary�I�v�V���i�����L�B�`���͕ʋL�̐������Q�ƁB
'recent_info'   => 'new.txt',
# ���������RSS�̃t�@�C����
'rss'           => 'index.rdf',
# XSLT�i�s�v�Ȃ�w�肵�Ȃ��Ă��悢�j
#'xslt'          => 'rss10general.xsl',
};


###############################
# �ݒ�͂����܂�
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
	# �ŐV����� �\�[�X����^�C�g���A�����N�A�������Ȃǂ𒊏o

	my $file = $conf->{filename}->{recent_info}; # �t�@�C����
	$file =~ s/[\<\>\|\`]//; # �悭�Ȃ��L��������
	$file =~ s/.*[\\\/]//; # �p�X������

	# ���̓t�@�C������C�ɓǂ݂���
	my $recent = '';
	{
		local $/;
		open(RECENT, "< $conf->{diary_dir}$file") || &error('can not open file.' . $!);
		$recent = <RECENT>;
		close(RECENT);
	}

	# �L�����Ƃɕ���
	my @entries = split /\Q$conf->{'separator'}->{'entry'}\E/, $recent;

	# regex
	my $re = q{^\s*(.*?)\s*\n} 
		. $conf->{'separator'}->{'date'} 
		. q{\s*(.*?)\s*\n} 
		. $conf->{'separator'}->{'title'} 
		. q{\s*(.*?)\s*\n} 
		. $conf->{'separator'}->{'body'} 
		. q{\s*(.*?)\s*\n$};

	# �L�����Ƃ̏���
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
		# content:encoded�̓T�j�^�C�Y���ĂȂ��B�\�[�X��M���H�H
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
	my $file = $conf->{filename}->{rss}; # �t�@�C����
	$file =~ s/[\<\>\|\`]//; # �悭�Ȃ��L��������
	$file =~ s/.*[\\\/]//; # �p�X������

	# �o��
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
	# �܂������i���Z���X�ȏ����ł���B�����Ėڂ��c�u���B
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
# ����
# a name did  [����|�Ȃ�]
# a name date [����|�Ȃ�]
# �ua name did�v�ua name date�v���Ȃ��Ƃ��Е�������
# a href did  [����|�Ȃ�]
# a href date [����|�Ȃ�]
# �ua href did�v�ua href date�v�Ƃ��ɂȂ����A�������͂����ꂩ�Е�������
# �����l      [�u"�v�ň͂܂�Ă���|�u'�v�ň͂܂�Ă���|�u���̒l�v]

	my $refanchor = shift;
	my $refchunk = shift;
	my($date, $time, $did, $dcdate, $akidate, $uri, $tb_uri);

	# uri��T���B
	if ($$refchunk =~ m|href\s*=\s*[\"\']?(\d{6}\.html#\d{8})(_\d{9,10})[\"\']?|) {
		$uri = $1 . $2;
	}

	# date��T���B
	$$refanchor =~ m/\D(\d{8})\D\D+/;
	$date = $1;

	# did��T���B
	$$refanchor =~ m/(id|name)\s*=\s*[\"\']?(\d{8})_(\d{9,10})[\"\']?/;
	$date = $date || $2;
	$time = $3;
	$did  = $2 . '_' . $3;

	&error('anchor is not detected.' . $!) unless defined $date;

	# uri��dcdate������Buri��date����g�ݗ��Ă�
	if     (defined $time && defined $date) {
		$uri    = $uri || &date2uri($date);
		$dcdate = &time2dcdate($time, $date);
	} elsif (defined $date) {
		$uri    = $uri || &date2uri($date);
		$dcdate = &date2dcdate($date);
	} else {
		&error('date is not detected.');
	}

	# Akiary�ɂ��ϊ����ꂽ���t��T���B
	$akidate = delete_tag($$refchunk);

	# tb_uri��T���B����͔ėp�I�ł͂Ȃ��c���ʂ̓v���g�^�C�v�B
	if ($$refchunk =~ m/href="(\S+?)"([^>]*?)>WikiBack\//) {
		$tb_uri = $1 || '';
	}

	return ($uri, $dcdate, $akidate, $tb_uri);
}


sub delete_tag {
	my $str = shift;

	# <br />�^�O��ۑ�����
	$str =~ s/(&lt;|<)\s*[b|B][r|R].*?(&gt;|>)/\0/g;

	## via: http://www.din.or.jp/~ohzaki/perl.htm
	# HTML�^�O�̐��K�\�� $tag_regex
	my $tag_regex_ = q{[^"'<>]*(?:"[^"]*"[^"'<>]*|'[^']*'[^"'<>]*)*(?:>|(?=<)|$(?!\n))}; #'}}}}
	my $comment_tag_regex = '<!(?:--[^-]*-(?:[^-]+-)*?-(?:[^>-]*(?:-[^>-]+)*?)??)*(?:>|$(?!\n)|--.*$)';
	my $tag_regex = qq{$comment_tag_regex|<$tag_regex_};
	my $text_regex = q{[^<]*};

	# $str �̒��̃^�O���폜���� $result �����
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
	# �������ꕶ���������i���{��Ή��B�����R�[�h��EUC�Ƃ���j
	my $result = shift;
	my($ret, $i) = ('', '0');
	while ($result =~ /([\xa1-\xfe]{2}|\x8e[\xa1-\xdf]|\x8f[\xa1-\xfe]{2}|.)/g) {
		$ret .= $1;
		if ($1 =~ /(�B|�D)/) {
			$ret .= "\n";
			last if $i++ > int($conf->{desc_limit});
		}
		last if $i++ > int($conf->{desc_limit_hard});
	}
	return $ret
}


## via: http://niaou.alib.jp/diary/diary-10-2003C.html#diary-10-21-2003-A
# (c) 1999-2003 NiAOU All Rights Reserved.
# $_ �̒��g�� utf-8 �ł��邱�Ƃ��O��B
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
# hint: uft-8 �̈ꕶ���̐��K�\��
#   [\x00-\x7F]|
#   [\xC0-\xDF][\x80-\xBF]|
#   [\xE0-\xEF][\x80-\xBF][\x80-\xBF]|
#   [\xF0-\xF7][\x80-\xBF][\x80-\xBF][\x80-\xBF]|
#   [\xF8-\xFB][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF]|
#   [\xFC-\xFD][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF]


## via: http://hasunuma.pobox.ne.jp/support/cyclamen.cgi?log=perl&tree=r20
# Shift_JIS�S�p�����Ή��� substr �֐�
# �����F������A�J�n�ʒu�A�������A�I�v�V�����i�J�n�ʒu�A�������̂����ꂩ���ȗ��j
# �S�p������2�����Ƃ��Đ����܂��B
# ��4������2�Ƃ����ꍇ�ɂ́A�S�p������1�����Ƃ��Đ�����悤�ɂ��܂����B
# ��4������1��^�����ꍇ�ɂ́A�؂�o�������ʂ̕�����̐擪��2�o�C�g������2�o�C�g�ڂɂ�����ꍇ�ƏI�[��2�o�C�g������1�o�C�g�ڂɂ�����ꍇ�ɂ́A���ꂼ��𔼊p�X�y�[�X�ɒu�������ĕԂ���镶�����̒��덇�킹���s���悤�ɂ��܂����B
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
