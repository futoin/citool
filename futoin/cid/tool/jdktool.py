
import os, glob

from ..buildtool import BuildTool

class jdkTool( BuildTool ):
    def getDeps( self ) :
        return ['jre']
    
    def _envNames( self ) :
        return ['jdkBin', 'jdkVer']
    
    def _installTool( self, env ):
        if 'jdkVer' in env:
            ver = env['jdkVer'].split('.')[0]
            self._requireDeb(['openjdk-{0}-jdk'.format(ver)])
            self._requireYum(['java-1.{0}.0-openjdk-devel'.format(ver)])
            self._requireZypper(['java-1_{0}_0-openjdk-devel'.format(ver)])
            self._requirePacman(['jdk{0}-openjdk'.format(ver)])
            self._requireEmerge(['=dev-java/oracle-jdk-bin-1.{0}*'.format(ver)])
        else:
            self._requireDeb(['default-jdk'])
            self._requireYum(['java-1.8.0-openjdk-devel'])
            self._requireZypper(['java-1_8_0-openjdk-devel'])
            self._requirePacman(['jdk8-openjdk'])
            self._requireEmerge(['virtual/jdk'])
    
    def uninstallTool( self, env ):
        pass

    def initEnv( self, env ) :
        if 'jdkBin' in env or 'jdkVer' not in env:
            super(jdkTool, self).initEnv( env, 'javac' )
            return
        
        env.setdefault('jdkVer', '8')
        ver = env['jdkVer'].split('.')[0]
        
        candidates = [
            # Debian / Ubuntu
            "/usr/lib/jvm/java-{0}-openjdk*/bin/javac".format(ver),
            # RedHat
            "/usr/lib/jvm/java-1.{0}.0/bin/javac".format(ver),
            # OpenSuse
            "/usr/lib*/jvm/java-1.7.0/bin/javac".format(ver),
            # Default oracle
            "/opt/jdk/jdk1.{0}*/bin/javac".format(ver),
        ]
        
        for c in candidates:
            bin_name = glob.glob(c)
            
            if bin_name:
                env['jdkBin'] = bin_name[0]
                self._have_tool = True
                break