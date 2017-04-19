
import os
import subprocess
import tempfile

from ..vcstool import VcsTool
from .bashtoolmixin import BashToolMixIn

class gitTool( BashToolMixIn, VcsTool ):
    """Git distributed version control system.
    
Home: https://git-scm.com/

Git tool forcibly sets user.email and user.name, 
if not set by user.
"""    
    def getDeps(self):
        return ['bash', 'tar']

    def autoDetectFiles( self ) :
        return '.git'
    
    def _installTool( self, env ):
        self._requirePackages(['git'])
        self._requireEmerge(['dev-vcs/git'])
        self._requirePacman(['git'])
        self._requireHomebrew('git')

    def _checkGitConfig( self, env ):
        gitBin = env['gitBin']
        user_email = None
        user_name = None
        
        try:
            user_email = self._callExternal([
                gitBin, 'config', 'user.email',
            ], verbose=False).strip()
        except:
            pass
        
        try:
            user_name = self._callExternal([
                gitBin, 'config', 'user.name',
            ], verbose=False).strip()
        except:
            pass
        
        if not user_email:
            self._info('Setting fallback user.email for repo')
            self._callExternal([
                gitBin, 'config', 'user.email',
                env.get('gitUserEmail', 'noreply@futoin.org')
            ])

        if not user_name:
            self._info('Setting fallback user.name for repo')
            self._callExternal([
                gitBin, 'config', 'user.name',
                env.get('gitUserName', 'FutoIn CITool')
            ])
            
    def _getCurrentBranch( self, config ):
        return self._callExternal( [
            config['env']['gitBin'], 'rev-parse', '--abbrev-ref', 'HEAD'
        ], verbose=False ).strip()

    def vcsGetRepo( self, config, wc_dir=None ):
        git_dir = wc_dir or os.path.join(os.getcwd(), '.git')
        
        return self._callExternal( [
            config['env']['gitBin'],
            '--git-dir={0}'.format(git_dir),
            'config',
            '--get',
            'remote.origin.url'
        ], verbose=False ).strip()
    
    def _gitCompareRepo( self, cfg, act ):
        return cfg == act or ('ssh://'+cfg) == act
    
    def vcsCheckout( self, config, vcs_ref ):
        gitBin = config['env']['gitBin']
        wc_dir = os.getcwd()
        vcsRepo = config['vcsRepo']
        vcs_ref = vcs_ref or 'master'
        
        if os.path.isdir( '.git' ):
            remote_url = self.vcsGetRepo( config, '.git')
            
            if not self._gitCompareRepo( vcsRepo, remote_url ) :
                self._errorExit( "Git remote mismatch: '{0}' != '{1}'"
                    .format(vcsRepo, remote_url ) )

            self._callExternal( [ gitBin, 'fetch', '-q'  ] )
        else :
            self._callExternal( [ gitBin, 'clone', '-q', vcsRepo, wc_dir ] )
            
            try:
                self._callExternal( [ gitBin, 'rev-parse', 'HEAD' ], verbose=False )
            except subprocess.CalledProcessError:
                # exit on empty repository
                return
            
        remote_branch = self._callExternal( [
            gitBin, 'branch', '-q', '--all', '--list', 'origin/'+vcs_ref
        ], verbose=False ).strip()
            
        if self._callExternal( [ gitBin, 'branch', '-q', '--list', vcs_ref ], verbose=False ).strip():
            self._callExternal( [ gitBin, 'checkout', '-q', vcs_ref ] )

            if remote_branch:
                self._callExternal( [ gitBin, 'branch', '-q', '--set-upstream-to', 'origin/'+vcs_ref ] )
                self._callExternal( [ gitBin, 'rebase', 'origin/'+vcs_ref  ] )
        elif remote_branch:
            self._callExternal( [ gitBin, 'checkout', '-q', '--track', '-b', vcs_ref, 'origin/'+vcs_ref ] )
        else:
            self._callExternal( [ gitBin, 'checkout', '-q', vcs_ref ] )
    
    def vcsCommit( self, config, message, files ):
        env = config['env']
        gitBin = env['gitBin']
        self._checkGitConfig(env)

        if files:
            self._callExternal( [ gitBin, 'add' ] + files )
        else:
            self._callExternal( [ gitBin, 'add', '-A' ] )
            files = []

        self._callExternal( [ gitBin, 'commit', '-q', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'tag', '-a', '-m', message, tag ] )
    
    def vcsPush( self, config, refs, repo=None, check_empty=True ):
        refs = refs or []
        gitBin = config['env']['gitBin']
        repo = repo or 'origin'
        
        if check_empty:
            try:
                self._callExternal( [ gitBin, 'rev-parse', 'HEAD' ], verbose=False )
            except subprocess.CalledProcessError:
                # exit on empty repository
                return

        self._callExternal( [ gitBin, '-c', 'push.default=current', 'push', '-q', repo ] + refs )
        
    def vcsGetRevision( self, config ) :
        gitBin = config['env']['gitBin']
        return self._callExternal( [
            gitBin, 'rev-parse', 'HEAD'
        ], verbose=False ).strip()
    
    def vcsGetRefRevision( self, config, vcs_cache_dir, branch ) :
        res = self._callExternal( [
            config['env']['gitBin'],
            'ls-remote', '--refs',
            config['vcsRepo'],
            'refs/heads/{0}'.format(branch)
        ], verbose=False ).strip()
        
        if res:
            return res.split()[0]
        
        self._errorExit( "Uknown Git ref: '{0}'".format( branch ) )
    

    def vcsListTags( self, config, vcs_cache_dir, tag_hint ) :
        if tag_hint:
            tag_hint = ['refs/tags/{0}'.format(tag_hint)]
        else:
            tag_hint = []
        
        res = self._callExternal( [
            config['env']['gitBin'],
            'ls-remote','--tags', '--refs',
            config['vcsRepo']
        ] + tag_hint, verbose=False ).strip().split("\n")

        res = [ v and v.split()[1].replace('refs/tags/', '') or '' for v in res ]
        res = list(filter(None, res))
        return res
    
    def vcsListBranches( self, config, vcs_cache_dir, branch_hint ) :
        if branch_hint:
            branch_hint = ['refs/heads/{0}'.format(branch_hint)]
        else:
            branch_hint = []
        
        res = self._callExternal( [
            config['env']['gitBin'],
            'ls-remote','--heads', '--refs',
            config['vcsRepo']
        ] + branch_hint, verbose=False ).strip().split("\n")

        res = [ v and v.split()[1].replace('refs/heads/', '') or '' for v in res ]
        res = list(filter(None, res))
        return res

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        env = config['env']
        gitBin = env['gitBin']
        vcsRepo = config['vcsRepo']

        if vcs_cache_dir is None:
            cache_repo = vcsRepo
        else:
            if os.path.exists(vcs_cache_dir):
                remote_url = self.vcsGetRepo( config, vcs_cache_dir )
                
                if not self._gitCompareRepo(vcsRepo,  remote_url):
                    self._warn('removing git cache on remote URL mismatch: {0} != {1}'
                        .format(remote_url, vcsRepo))
                    self._rmTree(vcs_cache_dir)
            
            if not os.path.exists(vcs_cache_dir):
                self._callExternal( [
                    env['gitBin'],
                    'clone',
                    '--mirror',
                    '--depth=1',
                    '--no-single-branch',
                    vcsRepo,
                    vcs_cache_dir
                ] )
            else:
                self._callExternal( [
                    env['gitBin'],
                    '--git-dir={0}'.format(vcs_cache_dir),
                    'fetch'
                ] )
                
            cache_repo = 'file://' + vcs_cache_dir
            
        if os.path.exists(dst_path):
            self._rmTree(dst_path)

        os.mkdir(dst_path)
        
        self._callBash(env, '{0} archive --remote={1} --format=tar {2} | {3} x -C {4}'
                .format(config['env']['gitBin'], cache_repo, vcs_ref, env['tarBin'], dst_path))

    def vcsBranch( self, config, vcs_ref ):
        env = config['env']
        gitBin = env['gitBin']
        
        self._callExternal( [
            config['env']['gitBin'],
            'checkout', '-b', vcs_ref,
        ] )
        
        self.vcsPush(config, [vcs_ref])

    def vcsMerge( self, config, vcs_ref, cleanup ):
        curr_ref = self._getCurrentBranch( config )
        
        env = config['env']
        gitBin = env['gitBin']
        
        try:
            self._callExternal( [
                config['env']['gitBin'],
                'merge', '--no-ff', 'origin/'+vcs_ref,
            ] )
        except subprocess.CalledProcessError:
            if cleanup:
                self.vcsRevert(config)
                self._errorExit('Merge failed, aborted.')
            self._errorExit('Merge failed, left as-is.')
        
        self.vcsPush(config, [curr_ref])

    def vcsDelete( self, config, vcs_cache_dir, vcs_ref ):
        env = config['env']
        gitBin = env['gitBin']
        
        have_local = (os.path.exists('.git') and
                      self._gitCompareRepo(config['vcsRepo'],  self.vcsGetRepo(config)))
        
        if have_local:
            try:
                self._callExternal( [
                    config['env']['gitBin'],
                    'branch', '-D', vcs_ref,
                ] )
            except subprocess.CalledProcessError as e:
                self._warn(str(e))
                
            self.vcsPush(config, ['--force', '--delete', vcs_ref])
                
            self._callExternal( [
                config['env']['gitBin'],
                'fetch', '--all', '--prune',
            ] )
        else:
            # a dirty hack to avoid error message of not found
            # local git repo
            repo = tempfile.mkdtemp('fakegit', dir='.')
            
            self._callExternal( [
                config['env']['gitBin'],
                'init', repo,
            ], verbose=False )

            oldcwd = os.getcwd()
            os.chdir(repo)
            self.vcsPush(config, ['--force', '--delete', vcs_ref], config['vcsRepo'], False)
            os.chdir(oldcwd)

            self._rmTree(repo)

    def vcsRevert( self, config):
        if os.path.exists(os.path.join('.git', 'MERGE_HEAD')):
            self._callExternal( [
                config['env']['gitBin'],
                'merge', '--abort',
            ] )

        self._callExternal( [
            config['env']['gitBin'],
            'reset', '--hard',
        ] )

    def vcsIsMerged( self, config, vcs_ref ):
        res = self._callExternal( [
            config['env']['gitBin'],
            'branch', '-r', '--merged', 'HEAD', 'origin/{0}'.format(vcs_ref)
        ], verbose=False ).strip()
        return res != ''
    
