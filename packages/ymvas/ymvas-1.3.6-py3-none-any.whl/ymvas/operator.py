from functools import lru_cache
import json
import os, sys
from os.path import join, relpath, exists
from ymvas.services import (
    Creator,
    Compiler
)
from .settings import Settings
from .utils    import system , YException, find_root



class Operator( Settings ):

    INIT_CHOICES   = ["default" , "account", "local"]
    CONFIG_CHOICES = ["set","get","show", "rm", "designate"]

    CONFIG_FLAGS = [
        ["global-compile-dir" , "where the compiles will be stored"    ],
        ["global-commands"    , "where global commands are stored"     ],
        ["global-src"         , "where the user repo is stored"        ],

        # server settings
        ['ymvas-compile-url'  , "url typically https://docs.ymvas.com" ],
        ['ymvas-domain'       , "domain typically ymvas.com, change it if you have  your host" ],
        ['ymvas-access'       , "access privileges"                    ],
    ]

    TASK_CHOICES = ["get","list"]



    def __init__( self, src:str = ""):
        self._argv = sys.argv[1:]
        self._fond = []
        self._src  = src

        Settings.__init__(self,self.src)
        
        if self.is_main:
            system.setup_global_config(**{ "global-src" : self.root })
        else:
            system.setup_global_config()

    # flags
    @property
    @lru_cache
    def version(self) -> bool | None:
        # expect version as postion 0
        return self._flag('-v','--version',0)

    @property
    @lru_cache
    def src(self) -> str:

        if self.version is True:
            return self._src
        

        is_init  = self.init is not None
        is_conf  = self.config is not None
        is_task  = self.task is not None
        sr_after = 0

        if is_init or is_conf:
            # src needs to be palced after base commands
            # in some cases like init or config
            sr_after = 2
        
        src = self._key_flag( "-s" , "--src" , after = sr_after )
        src = src if src is not None else self._src
        
        if is_init or is_conf:
            # for init with don't need to use global src 
            return src

        root, is_repo = find_root( src )
        if is_repo:
            return root

        _cnf = system.get_global_config()
        _exp = YException('invalid-directory', amsg={"src":src})

        if _cnf is None:
            raise _exp

        root = _cnf.get("global-src")
        if not isinstance(root,str):
            raise _exp

        return root
    
    @property
    @lru_cache
    def is_global(self) -> bool | None:
        if self.version is True:
            return None

        if self.init is not None:
            # can't use global for init
            return None
        
        # default case 
        src = self._key_flag("-s","--src")
        src = src if src is not None else self._src
        _, is_repo = find_root( src )

        if not is_repo:
            # is is not repo is global by default
            return True

        return self._flag("-g","--global")

    @property
    @lru_cache
    def debug(self) -> bool | None:
        return self._flag("-d","--debug")


    # arguments ---------------------------
    @property
    @lru_cache
    def init(self) -> str | None:
        args = self._argv

        if len(args) == 0 or args[0] != 'init':
            return

        if len(args) == 1 or args[1] not in self.INIT_CHOICES:
            raise YException(
                'init-help', amsg={
                "choices" : ",".join( self.INIT_CHOICES )
            })
        
        self._fond.append(('init',0))
        self._fond.append((args[1],1))
        return args[1]

    @property
    @lru_cache
    def config(self) -> tuple[str,dict[str,str]] | None:
        args = self._argv

        if len(args) == 0 or args[0] != 'config':
            return

        if len(args) == 1 or args[1] not in self.CONFIG_CHOICES:
            raise YException(
                'config-help', amsg={
                "choices" : ",".join( self.CONFIG_CHOICES ),
                "flags" : "\n".join(
                   [f"  {f'--{v}'.ljust(21)} {d}" for v,d in self.CONFIG_FLAGS]
                )
            })
        
        cmd = args[1]
        self._fond.append(('config',0))
        self._fond.append((cmd,1))

        if cmd == 'show':
            return cmd, {}

        if cmd == 'designate':
            return cmd, {}
        
        args = {}
        for k,_ in self.CONFIG_FLAGS:
            fg = f"--{k}"

            vl = self._key_flag(
                fg, fg, after=2
            ) if cmd == 'set' else self._flag(fg,fg)

            args[k] = vl
      
        return cmd,args

    @property
    @lru_cache
    def task(self) -> tuple[str,dict[str,str]] | None:
        args = self._argv

        if len(args) == 0 or args[0] != 'task':
            # if no extra args
            return

        if len(args) == 1 or args[1] not in self.TASK_CHOICES:
            raise YException(
                "task-help" , amsg={
                "choices" : ",".join( self.TASK_CHOICES ),

                # "flags" : "\n".join(
                #    [f"  {f'--{v}'.ljust(21)} {d}" for v,d in self.CONFIG_FLAGS]
                # )
            })
        
        cmd = args[1]
        self._fond.append(('task',0))
        self._fond.append((cmd,1))
      
      
        return cmd,{}
    
    @property
    @lru_cache
    def compile(self) -> str | None:
        args = self._argv

        if len(args) == 0 or args[0] != 'compile':
            return
        
        self._fond.append(("compile",0))
        cdir = self._key_flag("-c","--compile_dir",after=1)

        if cdir is not None:
            return cdir

        if self.source is not None:
            return join(self.source.git,'compile',self.alias)

        f = join(self.src,'compile',"0")

        cnt = 0
        while exists(f):
            cnt += 1
            f = join(self.src,f'compile',str(cnt))

        return f

    @property
    @lru_cache
    def command(self) -> str | None:
        args = self._argv

        if len(args) == 0:
            return

        for c in self.commands:
            if c['cmd'] != args[0]:
                continue
            
            return c['run'] + " " + c["path"]
        
        return None
        



    # actions
    def use_task(self):
        conf = self.get_repo_tasks_config()
        
        if self.task is None:
            return

        cmd = self.task[0]
        
        if cmd == 'get':
            tasks = conf.list()
            
            if len(tasks) == 0:
                print('no tasks here')
                return

            for i, task in enumerate(tasks):
                rl = relpath(task.src, self.d_tasks)
                print( f" {i} " + rl )
            
            selected = None
            while selected is None:
                task = input(" - select a task from this list or type `q` to exit:")
                
                if task == 'q':
                    exit()

                if not task.isnumeric() or len(tasks) <= int(task):
                    print(f'\033[31m - invalid selection [{task}] \033[0m')
                    continue

                selected = int(task)

            t = tasks[selected]
            
            print("")
            for s in t.bs_udfs():
                print((" " * s.level) + s.display())

            return

        if cmd == 'list':
            tasks = conf.list()

            for task in tasks:
                rl = relpath(task.src, self.d_tasks)
                print( "   " + rl )

            return
        
        raise YException(
                'task-help', amsg={
                "choices" : ",".join( self.TASK_CHOICES ),
                # "flags" : "\n".join(
                #    [f"  {f'--{v}'.ljust(21)} {d}" for v,d in self.CONFIG_FLAGS]
                # )
        })

    # actions
    def use_config(self):
        if self.config is None:
            return

        non_global_valid = [ "designate" ]

        if not self.is_global:
            cmd = self.config[0]

            if cmd in non_global_valid:

                if cmd == 'designate':
                    if not self.is_repo:
                        print("can't designate this directory as it's not a repositoy!")
                        return 

                    system.setup_global_config(
                        force=True,
                        **{
                        "global-src" : self.root,
                        "global-commands" : self.d_commands
                    })

                    return

                return

            print(f'[{cmd}] not configured (currently only avaliable globally), use --global tag')
            return

        stg = system.get_global_config()
        if self.config[0] == 'set':
            system.update_global_config(**self.config[1])
        elif self.config[0] == 'rm':
            items = {k:v for k,v in self.config[1].items() if v is not None }
            for k,_ in items.items():
                if k not in stg: continue
                del stg[k]
            system.update_global_config(**stg)
        elif self.config[0] == "get":
            items = {k:v for k,v in self.config[1].items() if v is not None }
            am = len(items)

            for k,_ in items.items():
                sg = stg.get(k,None)
                if am == 1:
                    print(sg)
                else:
                    print(f"{k} -> {sg}")
        else:
            print(json.dumps(stg,indent=2))

    
    def use_init(self):
        if self.init is None:
            return
        creator = Creator(
            self.init, 
            self.src
        )
        creator.run()
    
    def use_command(self):
        if self.command is None:
            return
        os.system(self.command)

    def use_compile(self):
        if self.compile is None:
            return

        data = Compiler( self , self.compile ).run()
        print(json.dumps( data , indent = 2 ))
        print('src ->',self.compile)
 
    

    # TODO
    @property
    @lru_cache
    def clone(self) -> str | None:
        args = self._argv

        if len(args) == 0 or args[0] != 'clone':
            return

        if len(args) == 1 or args[1] not in self.INIT_CHOICES:
            raise YException(
                'init-help', amsg={
                "choices" : ",".join( self.INIT_CHOICES )
            })
        
        return args[1]
        
    def use_clone(self):
        url = system.server_ssh_address.format(
            repo = args.repo
        )

        os.system(f"git clone {url}")
    
    def use_pull(self):
        modules = self.modules
        modules = {k:v for k,v in modules.items() if not v.is_main}

        os.system(f"{self._git} pull")
        for _,m in modules.items():
            os.system(f"{m._git} pull")



    


    # extras
    @property
    @lru_cache
    def commands(self) -> list:
        if not self.is_repo:
            return []

        if self.is_global:
            cnf = system.get_global_config()
            cmp = cnf.get('global-commands',None)
            if cmp is not None:
                self.d_commands = cmp

        if not exists(self.d_commands):
            return []
     
        settings = self.get_repo_comands_config()
        return settings.list()

      
    def __repr__(self) -> str:
        max_key = 21

        def justify(key:str, desc:str="",minus=0):
            nonlocal max_key
            desc = desc.replace('\n', (" " * (max_key-minus)) + "\n" )
            return f"{key.ljust(max_key-minus)} {desc}"

        extra = ""
        if self.is_repo:
            cmds = [(
                c['cmd'],
                (
                    "-> " + relpath(c['path'],self.d_commands) 
                    if c['desc'] is None else c['desc']
                )
            ) for c in self.commands ]

            max_cmd = max(len(x[0]) for x in cmds) if len(cmds) > 0 else 0
            max_key = max_key if max_cmd < max_key else max_cmd + 2
            
            meta = "" if not self.is_ymvas and not self.is_main else (
                f"{'Y' if self.is_ymvas else ''}"
                f"{'M' if self.is_main else ''}"
            )

            extra = (
                f"  - [ \033[1;32m{self.alias}\033[0m arguments ] {meta}"
                "\n    "
                + ("\n    ".join( justify(x,d,2) for x,d in cmds )) + "\n"
                "\n"
            )

        return (
            "Ymvas - handle your life like a developer!"
            "\n\n"
            "positional arguments:"
            "\n"
            "  - [ default arguments ]"
            "\n"
            f"    {justify('init','setup template for current directory',2)} \n"
            f"    {justify('config','edit configuration',2)} \n"
            f"    {justify('task','mange your project tasks',2)} \n"
            f"    {justify('compile','build endpoints locally',2)} \n"
            "\n"
            +extra+
            "options:"
            "\n"
            f"  {justify('-h, --help', 'show this help message and exit')} \n"
            f"  {justify('-v, --version', 'show version')} \n"
            f"  {justify('-g, --global')}"
            f"use the global configuration from \"{system.global_config_file()}\"\n"
        )

    def print_help(self) -> None:
        print(self)
    




    # utils
    def _flag(
            self,
            short:str,
            argument:str,
            position:int | None = None
        ) -> bool | None:

        if position is not None:
            if len(self._argv) <= position:
                return
            v = self._argv[position]
            x = ( v == short or v == argument )
            if x is True:
                self._fond.append(v)
            return x

        for i, a in enumerate(self._argv):
            if a == argument or a == short:
                self._fond.append((a,i))
                return True

        return 
        
    def _key_flag(
        self,
        short : str,
        argument : str,
        position : int | None = None,
        after : int = 0
    ) -> str | None:
        
        args = self._argv[after:]

        if position is not None:
            if len(args) <= position:
                return
            
            a = args[position]
            k = a.split('=')[0]
            if not (k == argument or k == short):
                return

            v = a.replace(k + "=", "")
            if len(v) > 2 and v[0] == v[-1] and v[0] in ["'",'"']:
                v = v.strip(v[0])

            self._fond.append((a,position))
            return v


        for i, a in enumerate(args):
            if not ( a.startswith(argument) or a.startswith(short) ):
                continue

            k = a.split('=')[0]
            if not (k == argument or k == short):
                continue

            v = a.replace(k + "=", "")
            if len(v) > 2 and v[0] == v[-1] and v[0] in ["'",'"']:
                v = v.strip(v[0])

            self._fond.append((a,i+after))
            return v
        
        return 


