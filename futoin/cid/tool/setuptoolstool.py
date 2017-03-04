
import os, shutil

from ..buildtool import BuildTool

class setuptoolsTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'setup.py' ]
        )
    
    def getDeps( self ) :
        return [ 'python', 'pip', 'venv' ]
    
    def _installTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', 'setuptools' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', '--upgrade', 'setuptools' ] )
        
    def uninstallTool( self, env ):
        pass
        
    def initEnv( self, env ):
        venv_dir = env['venvDir']
        self._have_tool = os.path.exists(os.path.join(venv_dir, 'bin', 'easy_install'))

    def onBuild( self, config ):
        for d in ['build', 'dist']:
            if os.path.exists(d):
                shutil.rmtree(d)

        pythonBin = config['env']['pythonBin']
        self._callExternal( [ pythonBin, 'setup.py', 'sdist', 'bdist_wheel' ] )
    
    