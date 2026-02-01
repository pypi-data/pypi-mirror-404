from .common import *
from kcws import kcws
def cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr='kcwebs'):
    "脚本入口"
    
    cmd_par=kcws.get_cmd_par(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)
    if cmd_par and not cmd_par['project']:
        cmd_par['project']='kcwebs'
    if cmd_par and cmd_par['install'] and not cmd_par['help']:#插入 应用、模块、插件
        if cmd_par['appname']:
            remppath=os.path.split(os.path.realpath(__file__))[0]
            if not os.path.exists(cmd_par['project']+'/'+cmd_par['appname']) and not os.path.exists(cmd_par['appname']):
                shutil.copytree(remppath+'/tempfile/kcwebs',cmd_par['project'])
                print('kcwebs项目创建成功')
            else:
                return kcws.cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)
        else:
            return kcws.cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)
    elif cmd_par:
        return kcws.cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)