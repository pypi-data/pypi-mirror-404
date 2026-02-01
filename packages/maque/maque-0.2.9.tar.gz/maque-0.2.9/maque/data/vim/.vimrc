" =============================================================================
" 服务器环境基础 Vim 配置
" 版本: 1.0
" 兼容性: Vim 7.4+
" 说明: 无插件依赖，适合服务器环境
" =============================================================================

" -----------------------------------------------------------------------------
" 基本设置
" -----------------------------------------------------------------------------
set nocompatible              " 关闭 Vi 兼容模式
set encoding=utf-8            " 内部编码 UTF-8
set fileencoding=utf-8        " 文件保存编码 UTF-8
set fileencodings=utf-8,gb2312,gbk,gb18030,latin1  " 文件读取编码顺序
set termencoding=utf-8        " 终端编码 UTF-8
set fileformats=unix,dos,mac  " 换行符格式优先级

syntax enable                 " 启用语法检测
syntax on                     " 开启语法高亮
filetype on                   " 开启文件类型检测
filetype plugin on            " 根据文件类型加载插件
filetype indent on            " 根据文件类型使用缩进规则

set number                    " 显示绝对行号
" set relativenumber            " 显示相对行号 (按需开启)
set ruler                     " 显示光标位置
set showcmd                   " 显示输入的命令
set showmode                  " 显示当前模式

set backspace=indent,eol,start  " 退格键正常工作
set whichwrap+=<,>,h,l,[,]    " 光标跨行移动
set mouse=a                   " 启用鼠标支持
set clipboard=unnamedplus     " 使用系统剪贴板 (Linux 用 + 寄存器)
set history=1000              " 命令历史记录数
set hidden                    " 允许切换未保存的缓冲区

" -----------------------------------------------------------------------------
" 缩进设置
" -----------------------------------------------------------------------------
set autoindent                " 新行继承缩进
set smartindent               " 智能缩进
set cindent                   " C风格缩进
set tabstop=4                 " Tab 显示宽度
set softtabstop=4             " Tab 编辑宽度
set shiftwidth=4              " 自动缩进宽度
set expandtab                 " Tab 转空格
set smarttab                  " 智能 Tab

" -----------------------------------------------------------------------------
" 搜索设置
" -----------------------------------------------------------------------------
set hlsearch                  " 高亮搜索结果
set incsearch                 " 增量搜索
set ignorecase                " 忽略大小写
set smartcase                 " 智能大小写
set wrapscan                  " 循环搜索

" -----------------------------------------------------------------------------
" 显示设置
" -----------------------------------------------------------------------------
set cursorline                " 高亮当前行
set showmatch                 " 高亮匹配括号
set matchtime=2               " 匹配括号高亮时间
set scrolloff=5               " 光标距顶部/底部保持5行
set sidescrolloff=10          " 光标距左右边缘保持10列
set wrap                      " 自动换行显示
set linebreak                 " 单词边界换行
set display=lastline          " 显示最后一行

set list                      " 显示不可见字符
set listchars=tab:▸\ ,trail:·,extends:>,precedes:<,nbsp:+

" 配色方案
try
    colorscheme desert
catch
endtry
set background=dark

" -----------------------------------------------------------------------------
" 状态栏设置
" -----------------------------------------------------------------------------
set laststatus=2              " 始终显示状态栏

set statusline=
set statusline+=%#PmenuSel#
set statusline+=\ %{mode()}
set statusline+=\ %#LineNr#
set statusline+=\ %f
set statusline+=%m%r%h
set statusline+=%=
set statusline+=%#CursorColumn#
set statusline+=\ %{&fileencoding?&fileencoding:&encoding}
set statusline+=\ [%{&fileformat}]
set statusline+=\ %y
set statusline+=\ %l/%L:%c
set statusline+=\ %p%%
set statusline+=\

" -----------------------------------------------------------------------------
" 命令行设置
" -----------------------------------------------------------------------------
set wildmenu                  " 命令行补全增强
set wildmode=longest:full,full
set wildignore=*.o,*.obj,*.pyc,*.class,*.swp,*~
set cmdheight=1

" -----------------------------------------------------------------------------
" 备份和撤销设置
" -----------------------------------------------------------------------------
set nobackup                  " 不创建备份文件
set nowritebackup
set noswapfile                " 不创建交换文件

" 持久化撤销历史
if has('persistent_undo')
    set undofile
    set undodir=~/.vim/undodir
    set undolevels=1000
    set undoreload=10000
    if !isdirectory($HOME . '/.vim/undodir')
        silent! call mkdir($HOME . '/.vim/undodir', 'p', 0700)
    endif
endif

" -----------------------------------------------------------------------------
" 窗口和分屏设置
" -----------------------------------------------------------------------------
set splitbelow                " 水平分屏在下方
set splitright                " 垂直分屏在右侧
set equalalways               " 分屏大小相等

" -----------------------------------------------------------------------------
" 性能优化
" -----------------------------------------------------------------------------
set lazyredraw                " 执行宏时不重绘
set ttyfast                   " 快速终端
set updatetime=300
set timeout
set timeoutlen=500
set ttimeoutlen=10

if exists('+synmaxcol')
    set synmaxcol=200         " 只对前200列语法高亮
endif

" -----------------------------------------------------------------------------
" 快捷键映射
" -----------------------------------------------------------------------------
let mapleader = " "
let g:mapleader = " "

" 文件操作
nnoremap <leader>w :w<CR>
nnoremap <leader>q :q<CR>
nnoremap <leader>x :x<CR>
nnoremap <leader>Q :qa!<CR>

" 搜索相关
nnoremap <leader><space> :nohlsearch<CR>

" 分屏操作
nnoremap <leader>sv :vsplit<CR>
nnoremap <leader>sh :split<CR>
nnoremap <leader>sc :close<CR>
nnoremap <leader>so :only<CR>

" 分屏导航
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l

" 调整窗口大小
nnoremap <C-Up> :resize +2<CR>
nnoremap <C-Down> :resize -2<CR>
nnoremap <C-Left> :vertical resize -2<CR>
nnoremap <C-Right> :vertical resize +2<CR>

" 缓冲区操作
nnoremap <leader>bn :bnext<CR>
nnoremap <leader>bp :bprevious<CR>
nnoremap <leader>bd :bdelete<CR>
nnoremap <leader>bl :ls<CR>
nnoremap <leader><tab> :b#<CR>

" 标签页操作
nnoremap <leader>tn :tabnew<CR>
nnoremap <leader>tc :tabclose<CR>
nnoremap <leader>to :tabonly<CR>
nnoremap gt :tabnext<CR>
nnoremap gT :tabprevious<CR>

" 行操作
nnoremap <leader>d dd
nnoremap <leader>y yy
nnoremap <A-j> :m .+1<CR>==
nnoremap <A-k> :m .-2<CR>==
vnoremap <A-j> :m '>+1<CR>gv=gv
vnoremap <A-k> :m '<-2<CR>gv=gv

" 快速编辑
inoremap jk <Esc>
inoremap kj <Esc>
nnoremap Y y$
nnoremap U <C-r>
nnoremap H ^
nnoremap L $
vnoremap H ^
vnoremap L $

" 粘贴模式切换（防止粘贴时自动缩进）
set pastetoggle=<F2>

" 文件浏览 (Lexplore 支持 toggle，再按一次关闭)
" %:p:h 表示当前文件所在目录
nnoremap <leader>e :Lexplore %:p:h<CR>

" 快速跳转标签页
nnoremap <leader>1 1gt
nnoremap <leader>2 2gt
nnoremap <leader>3 3gt
nnoremap <leader>4 4gt
nnoremap <leader>5 5gt

" 实用功能
nnoremap <leader>rc :source $MYVIMRC<CR>
nnoremap <leader>ec :edit $MYVIMRC<CR>
nnoremap <leader>a ggVG

" 运行当前文件 (结果在底部终端窗口显示，:q 关闭)
function! RunInTerminal(cmd)
    " 关闭已有的终端窗口
    for win in range(1, winnr('$'))
        if getbufvar(winbufnr(win), '&buftype') == 'terminal'
            execute win . 'wincmd c'
            break
        endif
    endfor
    " 打开新终端运行命令
    execute 'botright terminal ++rows=12 ' . a:cmd
endfunction

augroup run_file
    autocmd!
    autocmd FileType python     nnoremap <buffer> <leader>r :w<CR>:call RunInTerminal('python3 ' . expand('%'))<CR>
    autocmd FileType sh,bash    nnoremap <buffer> <leader>r :w<CR>:call RunInTerminal('bash ' . expand('%'))<CR>
    autocmd FileType javascript nnoremap <buffer> <leader>r :w<CR>:call RunInTerminal('node ' . expand('%'))<CR>
    autocmd FileType go         nnoremap <buffer> <leader>r :w<CR>:call RunInTerminal('go run ' . expand('%'))<CR>
    autocmd FileType rust       nnoremap <buffer> <leader>r :w<CR>:call RunInTerminal('cargo run')<CR>
augroup END

" 保持可视模式缩进
vnoremap < <gv
vnoremap > >gv

" -----------------------------------------------------------------------------
" 文件类型设置
" -----------------------------------------------------------------------------
augroup filetype_settings
    autocmd!

    " Python
    autocmd FileType python setlocal
        \ tabstop=4 softtabstop=4 shiftwidth=4 expandtab
        \ autoindent textwidth=120

    " YAML
    autocmd FileType yaml,yml setlocal
        \ tabstop=2 softtabstop=2 shiftwidth=2 expandtab

    " JSON
    autocmd FileType json setlocal
        \ tabstop=2 softtabstop=2 shiftwidth=2 expandtab

    " JavaScript / TypeScript
    autocmd FileType javascript,typescript,javascriptreact,typescriptreact setlocal
        \ tabstop=2 softtabstop=2 shiftwidth=2 expandtab

    " HTML / CSS
    autocmd FileType html,css,scss,less setlocal
        \ tabstop=2 softtabstop=2 shiftwidth=2 expandtab

    " Shell
    autocmd FileType sh,bash,zsh setlocal
        \ tabstop=4 softtabstop=4 shiftwidth=4 expandtab

    " Makefile
    autocmd FileType make setlocal noexpandtab tabstop=4 shiftwidth=4

    " Go
    autocmd FileType go setlocal noexpandtab tabstop=4 shiftwidth=4

    " Markdown
    autocmd FileType markdown setlocal wrap linebreak spell textwidth=80

    " Git commit
    autocmd FileType gitcommit setlocal textwidth=72 spell

augroup END

" -----------------------------------------------------------------------------
" 自动命令
" -----------------------------------------------------------------------------
augroup auto_commands
    autocmd!

    " 恢复上次光标位置
    autocmd BufReadPost *
        \ if line("'\"") > 1 && line("'\"") <= line("$") |
        \   execute "normal! g`\"" |
        \ endif

    " 保存时自动创建目录
    autocmd BufWritePre *
        \ if !isdirectory(expand('<afile>:p:h')) |
        \   call mkdir(expand('<afile>:p:h'), 'p') |
        \ endif

    " 保存时自动删除行尾空格 (保持光标位置)
    autocmd BufWritePre * let s:save_view = winsaveview() | %s/\s\+$//e | call winrestview(s:save_view)

    " 检查文件外部修改
    autocmd FocusGained,BufEnter * checktime

    " 高亮行尾空格
    autocmd InsertEnter * match ExtraWhitespace /\s\+\%#\@<!$/
    autocmd InsertLeave * match ExtraWhitespace /\s\+$/

augroup END

highlight ExtraWhitespace ctermbg=red guibg=red

" -----------------------------------------------------------------------------
" Netrw 文件浏览器设置
" -----------------------------------------------------------------------------
let g:netrw_banner = 0
let g:netrw_liststyle = 3
let g:netrw_browse_split = 4
let g:netrw_altv = 1
let g:netrw_winsize = 18

" netrw 中保持窗口导航快捷键
augroup netrw_mapping
    autocmd!
    autocmd FileType netrw nmap <buffer> <C-h> <C-w>h
    autocmd FileType netrw nmap <buffer> <C-l> <C-w>l
augroup END

" -----------------------------------------------------------------------------
" 其他设置
" -----------------------------------------------------------------------------
set confirm                   " 未保存退出时提示
set visualbell
set t_vb=
set belloff=all               " 禁用响铃

set autoread                  " 自动重新读取
set autowrite                 " 自动保存

set nojoinspaces
set nrformats-=octal          " 禁止将 007 等数字当作八进制处理

" 版本兼容
if v:version >= 800
    set nofixendofline
endif

if v:version >= 704
    set formatoptions+=j      " 合并行时删除注释符
endif

" -----------------------------------------------------------------------------
" 括号/引号自动配对
" -----------------------------------------------------------------------------
inoremap ( ()<Left>
inoremap [ []<Left>
inoremap { {}<Left>
inoremap " ""<Left>
inoremap ' ''<Left>

" 跳出右括号/引号 (Ctrl+l)
inoremap <expr> <C-l> search('\%#[]>)}''"`]', 'n') ? '<Right>' : '<Right>'

" -----------------------------------------------------------------------------
" 代码折叠
" 快捷键: za 切换, zR 全展开, zM 全折叠
" -----------------------------------------------------------------------------
set foldmethod=indent
set foldlevelstart=99

" -----------------------------------------------------------------------------
" Quickfix 导航
" -----------------------------------------------------------------------------
nnoremap ]q :cnext<CR>
nnoremap [q :cprev<CR>
nnoremap <leader>co :copen<CR>
nnoremap <leader>cc :cclose<CR>

" -----------------------------------------------------------------------------
" 搜索替换
" <leader>s: 替换光标下的单词
" -----------------------------------------------------------------------------
nnoremap <leader>s :%s/\<<C-r><C-w>\>//gc<Left><Left><Left>

" -----------------------------------------------------------------------------
" 会话管理
" -----------------------------------------------------------------------------
nnoremap <leader>ss :mksession! ~/.vim/session.vim<CR>
nnoremap <leader>sl :source ~/.vim/session.vim<CR>

" -----------------------------------------------------------------------------
" 快速注释 (<leader>/ 切换注释)
" 支持: Python/Shell(#), JS/Go/Rust/C(//), Vim("), Lua(--)
" -----------------------------------------------------------------------------
function! GetCommentString()
    let l:ft = &filetype
    if l:ft =~ 'python\|sh\|bash\|zsh\|ruby\|perl\|yaml\|toml\|make\|dockerfile'
        return '#'
    elseif l:ft =~ 'javascript\|typescript\|go\|rust\|c\|cpp\|java\|scala'
        return '//'
    elseif l:ft =~ 'vim'
        return '"'
    elseif l:ft =~ 'lua\|haskell'
        return '--'
    elseif l:ft =~ 'css\|scss'
        return '/* '
    else
        return '#'
    endif
endfunction

function! ToggleComment() range
    let l:cs = GetCommentString()
    let l:firstline = getline(a:firstline)
    " 检查是否已注释
    if l:firstline =~ '^\s*' . escape(l:cs, '/*')
        " 取消注释
        execute a:firstline . ',' . a:lastline . 's/^\(\s*\)' . escape(l:cs, '/*') . '\s\?/\1/e'
    else
        " 添加注释
        execute a:firstline . ',' . a:lastline . 's/^\(\s*\)/\1' . escape(l:cs, '/*&') . ' /e'
    endif
endfunction

nnoremap <leader>/ :call ToggleComment()<CR>
vnoremap <leader>/ :call ToggleComment()<CR>

" =============================================================================
" 配置结束
" =============================================================================
" 扩展配置 (LSP 插件) 见 lsp.vim
" 启用方法: 在 .vimrc 末尾添加 source ~/.vim/lsp.vim
" 或使用: maque system setup-vim --lsp
