
from js9 import j
# import os


app = j.tools.prefab._getBaseAppClass()


class PrefabGolang(app):

    NAME = 'go'

    def reset(self):
        self.prefab.bash.profileDefault.deletePathFromEnv("GOPATH")
        self.prefab.bash.profileDefault.deletePathFromEnv("GOROOT")
        self.prefab.bash.profileJS.deletePathFromEnv("GOROOT")

        self.prefab.bash.profileDefault.deleteAll("GOPATH")
        self.prefab.bash.profileJS.deleteAll("GOPATH")

        self.prefab.bash.profileDefault.deleteAll("GOROOT")
        self.prefab.bash.profileJS.deleteAll("GOROOT")

        self.prefab.bash.profileDefault.deleteAll("GOGITSDIR")
        self.prefab.bash.profileJS.deleteAll("GOGITSDIR")

        self.prefab.bash.profileDefault.pathDelete("/go/")
        self.prefab.bash.profileJS.pathDelete("/go/")

        # ALWAYS SAVE THE DEFAULT FIRST !!!
        self.prefab.bash.profileDefault.save()
        self.prefab.bash.profileJS.save()

        app.reset(self)
        self._init()

    def _init(self):
        self.GOROOTDIR = self.prefab.core.dir_paths['GOROOTDIR']
        self.GOPATHDIR = self.prefab.core.dir_paths['GOPATHDIR']

    def isInstalled(self):
        rc, out, err = self.prefab.core.run("go version", die=False, showout=False, profile=True)
        if rc > 0 or "1.8" not in out:
            return False
        if self.doneGet("install") == False:
            return False
        return True

    def install(self, reset=False):
        if reset is False and self.isInstalled():
            return
        if self.prefab.core.isMac:

            downl = "https://storage.googleapis.com/golang/go1.8.1.darwin-amd64.tar.gz"
        elif "ubuntu" in self.prefab.platformtype.platformtypes:
            downl = "https://storage.googleapis.com/golang/go1.8.1.linux-amd64.tar.gz"
        else:
            raise j.exceptions.RuntimeError("platform not supported")
        self.prefab.core.run(cmd=self.replace("rm -rf $GOROOTDIR"), die=True)
        self.prefab.core.dir_ensure(self.GOROOTDIR)
        self.prefab.core.dir_ensure(self.GOPATHDIR)

        profile = self.prefab.bash.profileDefault
        profile.envSet("GOROOT", self.GOROOTDIR)
        profile.envSet("GOPATH", self.GOPATHDIR)
        profile.addPath(self.prefab.core.joinpaths(self.GOPATHDIR, 'bin'))
        profile.addPath(self.prefab.core.joinpaths(self.GOROOTDIR, 'bin'))
        profile.save()

        self.prefab.core.file_download(downl, self.GOROOTDIR, overwrite=False, retry=3,
                                        timeout=0, expand=True, removeTopDir=True)

        self.prefab.core.dir_ensure("%s/src" % self.GOPATHDIR)
        self.prefab.core.dir_ensure("%s/pkg" % self.GOPATHDIR)
        self.prefab.core.dir_ensure("%s/bin" % self.GOPATHDIR)

        self.get("github.com/tools/godep")
        self.goraml()
        self.glide()

        self.doneSet("install")

    def goraml(self):
        """
        Install (using go get) goraml and go-bindata.
        """
        C = '''
        go get -u github.com/Jumpscale/go-raml
        set -ex
        go get -u github.com/jteeuwen/go-bindata/...
        cd $GOPATH/src/github.com/jteeuwen/go-bindata/go-bindata
        go build
        go install
        cd $GOPATH/src/github.com/Jumpscale/go-raml
        sh build.sh
        '''
        self.prefab.core.execute_bash(C, profile=True)

    def glide(self):
        """
        install glide
        """
        if self.doneGet('glide'):
            return
        self.prefab.core.file_download('https://glide.sh/get', '$TMPDIR/installglide.sh', minsizekb=4)
        self.prefab.core.run('. $TMPDIR/installglide.sh', profile=True)
        self.doneSet('glide')

    @property
    def GOPATH(self):
        return j.dirs.GOPATHDIR

    def clean_src_path(self):
        srcpath = self.prefab.core.joinpaths(self.GOPATH, 'src')
        self.prefab.core.dir_remove(srcpath)

    def get(self, url):
        """
        e.g. url=github.com/tools/godep
        """
        self.clean_src_path()
        self.prefab.core.run('go get -v -u %s' % url, profile=True)

    def godep(self, url, branch=None, depth=1):
        """
        e.g. url=github.com/tools/godep
        """
        self.clean_src_path()
        GOPATH = self.GOPATH

        pullurl = "git@%s.git" % url.replace('/', ':', 1)

        dest = self.prefab.development.git.pullRepo(pullurl,
                                                     branch=branch,
                                                     depth=depth,
                                                     dest='%s/src/%s' % (GOPATH, url),
                                                     ssh=False)
        self.prefab.core.run('cd %s && godep restore' % dest, profile=True)