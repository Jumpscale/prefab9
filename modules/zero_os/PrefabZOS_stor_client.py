from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZOS_stor_client(base):
    
    def _init(self):
        self.logger_enable()
        self.BUILDDIRL = self.core.replace("$BUILDDIR/buildg8client/")
        self.CODEDIRL = self.BUILDDIRL


    def install(self):
        """
        is for python 3.5 !
        """
        return self.prefab.runtimes.pip.install('http://home.maxux.net/wheelhouse/g8storclient-1.0-cp35-cp35m-manylinux1_x86_64.whl')

    def build(self,python_build=False):
        """
        js9 'j.tools.prefab.local.zero_os.zos_stor_client.build()'
        """
        self.prefab.tools.git.pullRepo('https://github.com/maxux/lib0stor', dest=self.CODEDIRL)
        self.prefab.core.run('cd {}; git submodule init; git submodule update'.format(self.CODEDIRL))

        if python_build:
            C= """
            set -ex
            cd $BUILDDIRL
            cd ../python3/
            . envbuild.sh
            cd $BUILDDIRL
            make -C src
            cd python/
            python3 setup.py build
            cd $BUILDDIRL

            """
            if self.core.isMac:
                libpath = "lib.macosx-10.13-x86_64-3.6/g8storclient.cpython-36m-darwin.so"
                C = C + "cp python/build/$libpath ../python3/lib/python3.6/lib-dynload/"
                C = C.replace("$libpath",libpath)

            C=self.replace(C)
            self.core.file_write("%s/build.sh"%self.BUILDDIRL,C)
            self.prefab.core.run("bash %s/build.sh"%self.BUILDDIRL)
        else:
            
            BUILDENV = """
            set -ex
            cd $CODEDIRL
            mkdir -p $BUILDDIRL
            """
            BUILDENV=self.replace(BUILDENV)

            if self.core.isMac:
                self.prefab.system.base.development(python=False)    

                C = """
                export LIBRARY_PATH="/usr/lib:/usr/local/lib"
                export LD_LIBRARY_PATH="/usr/lib:/usr/local/lib"
                export OPENSSLPATH=$(brew --prefix openssl)
                export CPPPATH="$OPENSSLPATH/include:/usr/include"
                export CPATH="$OPENSSLPATH/include:/usr/include"
                export PATH=$OPENSSLPATH/lib:/$OPENSSLPATH/bin:/usr/local/bin:/usr/bin:/bin
                export CFLAGS="-I$OPENSSLPATH/include -I/usr/include "
                export CPPFLAGS=$CFLAGS
                export LDFLAGS="-L/usr/lib -L/usr/local/lib -L$OPENSSLPATH/lib"

                echo $CFLAGS
                echo $LDFLAGS

                """  
                BUILDENV += self.replace(C)
            else:         
                self.prefab.system.package.ensure('build-essential libz-dev libssl-dev python3-dev libsnappy-dev')
                self.prefab.lib.cmake.install()


            self.core.file_write("/tmp/buildenv.sh",BUILDENV)
            self.prefab.core.run('source /tmp/buildenv.sh;make -C src')
            self.prefab.core.run('source /tmp/buildenv.sh; cd python/;python3 setup.py build')

