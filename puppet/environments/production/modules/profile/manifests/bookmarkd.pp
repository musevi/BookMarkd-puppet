class profile::bookmarkd (
  String $deploy_dir	= '/opt/bookmarkd',
  String $repo_url 	= 'https://github.com/musevi/BookMarkd-puppet.git',
  String $repo_ref	= 'main',
) {

  $api_host = $facts['networking']['ip']

  package { ['git', 'docker.io', 'docker-compose']:
    ensure => installed,
  }

  service { 'docker':
    ensure => running,
    # enable => true,
    require => Package[['docker.io', 'docker-compose']],
  }

  file { $deploy_dir:
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => '0755',
  }

  # Clone repo once
  exec { 'bookmarkd_clone':
    command => "git clone --branch ${repo_ref} ${repo_url} ${deploy_dir}",
    creates => "${deploy_dir}/.git",
    path => ['/usr/bin'],
    require => [Package['git'], File[$deploy_dir]],
  }

  # Update on subsequent runs
  exec { 'bookmarkd_update':
    command => "git fetch --all && git reset --hard origin/${repo_ref}",
    cwd => $deploy_dir,
    path => ['/usr/bin'],
    onlyif => "test -d ${deploy_dir}/.git",
    require => Exec['bookmarkd_clone'],
  }

  file { "${deploy_dir}/docker-compose.yml":
    ensure => file,
    owner => 'root',
    group => 'root',
    mode => '0644',
    content => epp('profile/docker-compose.yml.epp', { 'api_host' => $api_host }),
    require => Exec['bookmarkd_clone'],
  }

  exec { 'bookmarkd_compose_up':
    command => 'docker-compose up -d --build',
    cwd => $deploy_dir,
    path => ['/usr/bin'],
    require => [Service['docker'], File["${deploy_dir}/docker-compose.yml"], Exec['bookmarkd_update']],
  } 
}
  
