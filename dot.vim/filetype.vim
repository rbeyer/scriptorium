" Detect NAIF SPICE text kernel files
	if exists("did_load_filetypes")
	  finish
	endif
	augroup filetypedetect
	  au! BufRead,BufNewFile *.tf		setfiletype SPICE
	  au! BufRead,BufNewFile *.ti		setfiletype SPICE
	  au! BufRead,BufNewFile *.tls		setfiletype SPICE
	  au! BufRead,BufNewFile *.tpc		setfiletype SPICE
	  au! BufRead,BufNewFile *.tsc		setfiletype SPICE
	  au! BufRead,BufNewFile *.tm		setfiletype SPICE
	augroup END
