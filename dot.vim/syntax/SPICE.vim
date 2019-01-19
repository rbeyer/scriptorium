" Vim syntax file
" Language: NAIF SPICE text kernel files
" Maintainer: Ross Beyer <rbeyer@seti.org>

" quit when a syntax file was already loaded.
if exists("b:current_syntax")
  finish
endif

syntax region Comment
	\ start="\%^"
	\ end="^\s*\\begindata\s*$"

syntax region Comment
	\ start="^\s*\\begintext\s*$"
	\ end="^\s*\\begindata\s*$"

syntax region String
	\ start=+'+
	\ end=+'+

let b:current_syntax = "NAIF SPICE"
